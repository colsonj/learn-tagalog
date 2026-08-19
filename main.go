package main

import (
	"crypto/sha256"
	"embed"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync"
	"time"
)

//go:embed web data
var assets embed.FS

const appName = "TagTrain"
const fixedPort = 8873

var (
	progressMu   sync.Mutex
	lastPing     time.Time
	lastPingMu   sync.Mutex
	curriculumJS []byte
	buildVersion string // hash of embedded assets, so exe builds are distinguishable
)

// assetsVersion fingerprints the embedded content. Two different builds of the
// exe get different versions, letting a newer exe evict a stale running one.
func assetsVersion() string {
	h := sha256.New()
	fs.WalkDir(assets, ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		io.WriteString(h, path)
		b, _ := fs.ReadFile(assets, path)
		h.Write(b)
		return nil
	})
	return fmt.Sprintf("%x", h.Sum(nil))[:16]
}

func progressPath() string {
	exe, err := os.Executable()
	if err != nil {
		return "tagtrain-progress.json"
	}
	return filepath.Join(filepath.Dir(exe), "tagtrain-progress.json")
}

// buildCurriculum merges data/<level>/{meta,unitNN,exam}.json into one JSON blob.
func buildCurriculum() ([]byte, error) {
	type level struct {
		Meta  json.RawMessage   `json:"meta"`
		Units []json.RawMessage `json:"units"`
		Exam  json.RawMessage   `json:"exam"`
	}
	order := []string{"a1", "a2", "b1", "b2"}
	out := map[string]any{}
	var levels []level
	for _, lv := range order {
		dir := "data/" + lv
		entries, err := fs.ReadDir(assets, dir)
		if err != nil {
			return nil, fmt.Errorf("level %s missing: %w", lv, err)
		}
		var l level
		var unitNames []string
		for _, e := range entries {
			name := e.Name()
			b, err := fs.ReadFile(assets, dir+"/"+name)
			if err != nil {
				return nil, err
			}
			switch {
			case name == "meta.json":
				l.Meta = b
			case name == "exam.json":
				l.Exam = b
			case strings.HasPrefix(name, "unit") && strings.HasSuffix(name, ".json"):
				unitNames = append(unitNames, name)
			}
		}
		sort.Strings(unitNames)
		for _, name := range unitNames {
			b, err := fs.ReadFile(assets, dir+"/"+name)
			if err != nil {
				return nil, err
			}
			l.Units = append(l.Units, b)
		}
		if l.Meta == nil || l.Exam == nil || len(l.Units) == 0 {
			return nil, fmt.Errorf("level %s incomplete (meta=%v exam=%v units=%d)", lv, l.Meta != nil, l.Exam != nil, len(l.Units))
		}
		levels = append(levels, l)
	}
	out["levels"] = levels
	return json.Marshal(out)
}

func openBrowser(url string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	_ = cmd.Start()
}

func main() {
	var err error
	curriculumJS, err = buildCurriculum()
	if err != nil {
		log.Fatalf("curriculum error: %v", err)
	}
	buildVersion = assetsVersion()

	mux := http.NewServeMux()

	webFS, _ := fs.Sub(assets, "web")
	fileServer := http.FileServer(http.FS(webFS))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/audio/") && strings.HasSuffix(r.URL.Path, ".mp3") {
			// clip filenames are content hashes — safe to cache forever
			w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
		} else {
			// never serve a stale page/manifest after the exe is updated
			w.Header().Set("Cache-Control", "no-cache")
		}
		fileServer.ServeHTTP(w, r)
	})

	mux.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"app":%q,"version":%q}`, appName, buildVersion)
	})

	mux.HandleFunc("/api/curriculum", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.Write(curriculumJS)
	})

	mux.HandleFunc("/api/progress", func(w http.ResponseWriter, r *http.Request) {
		progressMu.Lock()
		defer progressMu.Unlock()
		switch r.Method {
		case http.MethodGet:
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
			b, err := os.ReadFile(progressPath())
			if err != nil {
				w.Write([]byte("{}"))
				return
			}
			w.Write(b)
		case http.MethodPost:
			var body json.RawMessage
			if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 8<<20)).Decode(&body); err != nil {
				http.Error(w, "bad json", 400)
				return
			}
			tmp := progressPath() + ".tmp"
			if err := os.WriteFile(tmp, body, 0644); err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			if err := os.Rename(tmp, progressPath()); err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			w.Write([]byte(`{"ok":true}`))
		default:
			http.Error(w, "method not allowed", 405)
		}
	})

	mux.HandleFunc("/api/ping", func(w http.ResponseWriter, r *http.Request) {
		lastPingMu.Lock()
		lastPing = time.Now()
		lastPingMu.Unlock()
		w.Write([]byte(`{"ok":true}`))
	})

	mux.HandleFunc("/api/quit", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(`{"ok":true}`))
		go func() {
			time.Sleep(300 * time.Millisecond)
			os.Exit(0)
		}()
	})

	addr := fmt.Sprintf("127.0.0.1:%d", fixedPort)
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		// Another instance is already on the port. If it's the same build,
		// just open a tab to it; if it's an older build, tell it to quit and
		// take over so the user always sees the exe they launched.
		var health struct{ App, Version string }
		if resp, herr := http.Get("http://" + addr + "/api/health"); herr == nil {
			json.NewDecoder(resp.Body).Decode(&health)
			resp.Body.Close()
		}
		if health.App == appName && health.Version == buildVersion {
			openBrowser("http://" + addr + "/")
			return
		}
		if health.App == appName {
			http.Post("http://"+addr+"/api/quit", "application/json", nil)
			for i := 0; i < 20 && err != nil; i++ {
				time.Sleep(250 * time.Millisecond)
				ln, err = net.Listen("tcp", addr)
			}
		}
		if err != nil {
			ln, err = net.Listen("tcp", "127.0.0.1:0")
			if err != nil {
				log.Fatal(err)
			}
		}
	}
	url := "http://" + ln.Addr().String() + "/"

	lastPing = time.Now()
	// Exit if no browser tab has pinged for a while (windowless on Windows,
	// so this is how the process avoids outliving the UI).
	go func() {
		for {
			time.Sleep(30 * time.Second)
			lastPingMu.Lock()
			idle := time.Since(lastPing)
			lastPingMu.Unlock()
			if idle > 5*time.Minute {
				os.Exit(0)
			}
		}
	}()

	log.Printf("%s running at %s (progress file: %s)", appName, url, progressPath())
	openBrowser(url)
	log.Fatal(http.Serve(ln, mux))
}
