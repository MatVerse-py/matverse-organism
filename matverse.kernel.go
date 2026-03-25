package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"
)

const tick = 3 * time.Second
const maxCells = 8192

type Cell struct {
	ID   int     `json:"id"`
	E    float64 `json:"e"`
	Psi  float64 `json:"ψ"`
}

var (
	cells    []Cell
	maxTick  = 1000
	curTick  int
	dataLock sync.RWMutex
)

func mutate() {
	dataLock.Lock()
	defer dataLock.Unlock()
	curTick++
	for i := range cells {
		cells[i].Psi = 1.0 - float64(curTick)/float64(maxTick)
		cells[i].E *= 0.999 // ligeiro decaimento
	}
	if curTick < maxTick && len(cells) < maxCells {
		cells = append(cells, Cell{
			ID:   len(cells),
			E:    1.0,
			Psi:  1.0 - float64(curTick)/float64(maxTick),
		})
	}
}

func procreate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var payload struct {
		Energy float64 `json:"energy"`
	}

	err := json.NewDecoder(r.Body).Decode(&payload)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	dataLock.Lock()
	defer dataLock.Unlock()

	if len(cells) < maxCells {
		newCell := Cell{
			ID:   len(cells),
			E:    payload.Energy,
			Psi:  1.0, // Initial Psi for new cell
		}
		cells = append(cells, newCell)
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(map[string]interface{}{"message": "Cell procreated", "id": newCell.ID})
	} else {
		http.Error(w, "Max cells reached", http.StatusServiceUnavailable)
	}
}

func getOrganismState(w http.ResponseWriter, r *http.Request) {
	dataLock.RLock()
	defer dataLock.RUnlock()

	state := map[string]interface{}{
		"tick":  curTick,
		"psi":   cells[0].Psi,
		"cells": len(cells),
	}
	json.NewEncoder(w).Encode(state)
}

func getCells(w http.ResponseWriter, r *http.Request) {
	dataLock.RLock()
	defer dataLock.RUnlock()

	json.NewEncoder(w).Encode(cells)
}

func main() {
	// Serve static files from the "web" directory
	http.Handle("/", http.FileServer(http.Dir("web")))

	// Initialize cells
	for i := 0; i < 686; i++ {
		cells = append(cells, Cell{ID: i, E: 1.0, Psi: 1.0})
	}

	// Start the mutation loop
	go func() {
		for range time.Tick(tick) {
			mutate()
		}
	}()

	// API endpoints
	http.HandleFunc("/api/organism/stream", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")
		for {
			dataLock.RLock()
			var buf bytes.Buffer
			json.NewEncoder(&buf).Encode(map[string]interface{}{
				"tick":  curTick,
				"ψ":     cells[0].Psi,
				"cells": len(cells),
			})
			dataLock.RUnlock()
			fmt.Fprintf(w, "data: %s\n\n", buf.String())
			w.(http.Flusher).Flush()
			time.Sleep(tick / 2)
		}
	})
	http.HandleFunc("/api/organism/state", getOrganismState)
	http.HandleFunc("/api/cells", getCells)
	http.HandleFunc("/api/cell/procreate", procreate)

	// Start the server
	log.Println("=> Matverse ouvindo em :8765")
	http.ListenAndServe(":8765", nil)
}
