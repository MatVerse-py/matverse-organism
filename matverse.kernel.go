package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"net/http"
	"sync"
	"time"
)

const tick = 3 * time.Second
const maxCells = 8192

type Cell struct {
	ID  int     `json:"id"`
	E   float64 `json:"e"`
	Psi float64 `json:"ψ"`
}

type OrganismVitals struct {
	Tick           int     `json:"tick"`
	Psi            float64 `json:"psi"`
	Cells          int     `json:"cells"`
	AvgEnergy      float64 `json:"avg_energy"`
	StressIndex    float64 `json:"stress_index"`
	LedgerHealth   float64 `json:"ledger_health"`
	Responsiveness float64 `json:"responsiveness"`
	Status         string  `json:"status"`
}

var (
	cells    []Cell
	maxTick  = 1000
	curTick  int
	dataLock sync.RWMutex
)

func computeVitals() OrganismVitals {
	totalEnergy := 0.0
	avgPsi := 1.0
	if len(cells) > 0 {
		avgPsi = 0.0
		for _, c := range cells {
			totalEnergy += c.E
			avgPsi += c.Psi
		}
		avgPsi = avgPsi / float64(len(cells))
	}

	avgEnergy := 0.0
	if len(cells) > 0 {
		avgEnergy = totalEnergy / float64(len(cells))
	}

	decay := float64(curTick) / float64(maxTick)
	if decay > 1.0 {
		decay = 1.0
	}
	stressIndex := math.Min(1.0, math.Max(0.0, (1.0-avgPsi)*0.6+(1.0-avgEnergy)*0.4))
	ledgerHealth := math.Max(0.0, 1.0-decay*0.2)
	responsiveness := math.Max(0.0, 1.0-stressIndex*0.8)

	status := "THRIVING"
	switch {
	case responsiveness <= 0.2:
		status = "UNRESPONSIVE"
	case stressIndex >= 0.8:
		status = "CRITICAL"
	case stressIndex >= 0.6:
		status = "STRESSED"
	case stressIndex >= 0.3:
		status = "HEALTHY"
	}

	return OrganismVitals{
		Tick:           curTick,
		Psi:            avgPsi,
		Cells:          len(cells),
		AvgEnergy:      avgEnergy,
		StressIndex:    stressIndex,
		LedgerHealth:   ledgerHealth,
		Responsiveness: responsiveness,
		Status:         status,
	}
}

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
			ID:  len(cells),
			E:   1.0,
			Psi: 1.0 - float64(curTick)/float64(maxTick),
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
			ID:  len(cells),
			E:   payload.Energy,
			Psi: 1.0, // Initial Psi for new cell
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

	state := computeVitals()
	json.NewEncoder(w).Encode(state)
}

func getOrganismVitals(w http.ResponseWriter, r *http.Request) {
	dataLock.RLock()
	defer dataLock.RUnlock()

	json.NewEncoder(w).Encode(computeVitals())
}

func getCells(w http.ResponseWriter, r *http.Request) {
	dataLock.RLock()
	defer dataLock.RUnlock()

	json.NewEncoder(w).Encode(cells)
}

func organismAct(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var payload struct {
		Action string  `json:"action"`
		Energy float64 `json:"energy"`
	}
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	dataLock.Lock()
	defer dataLock.Unlock()

	switch payload.Action {
	case "procreate":
		if len(cells) >= maxCells {
			http.Error(w, "Max cells reached", http.StatusServiceUnavailable)
			return
		}
		if payload.Energy <= 0 {
			payload.Energy = 1.0
		}
		cells = append(cells, Cell{ID: len(cells), E: payload.Energy, Psi: 1.0})
	case "stabilize":
		for i := range cells {
			cells[i].Psi = math.Min(1.0, cells[i].Psi+0.03)
			cells[i].E = math.Min(1.5, cells[i].E+0.05)
		}
	default:
		http.Error(w, "Unsupported action", http.StatusBadRequest)
		return
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "action applied",
		"action":  payload.Action,
		"state":   computeVitals(),
	})
}

func organismRepair(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	dataLock.Lock()
	defer dataLock.Unlock()

	if len(cells) == 0 {
		cells = append(cells, Cell{ID: 0, E: 1.0, Psi: 1.0})
	}
	for i := range cells {
		cells[i].Psi = math.Max(0.85, cells[i].Psi)
		cells[i].E = math.Max(0.90, cells[i].E)
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "repair applied",
		"state":   computeVitals(),
	})
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
	http.HandleFunc("/api/organism/vitals", getOrganismVitals)
	http.HandleFunc("/api/organism/act", organismAct)
	http.HandleFunc("/api/organism/repair", organismRepair)
	http.HandleFunc("/api/cells", getCells)
	http.HandleFunc("/api/cell/procreate", procreate)

	// Start the server
	log.Println("=> Matverse ouvindo em :8765")
	http.ListenAndServe(":8765", nil)
}
