document.addEventListener('DOMContentLoaded', () => {
    const tickSpan = document.getElementById('tick');
    const psiSpan = document.getElementById('psi');
    const cellsSpan = document.getElementById('cells');
    const procreateButton = document.getElementById('procreate-button');
    const cellsDataList = document.getElementById('cells-data');

    // Function to fetch all cells
    const fetchCells = async () => {
        try {
            const response = await fetch('/api/cells');
            const cells = await response.json();
            cellsDataList.innerHTML = ''; // Clear previous list
            cells.forEach(cell => {
                const listItem = document.createElement('li');
                listItem.textContent = `ID: ${cell.ID}, Energy: ${cell.E.toFixed(3)}, Psi: ${cell.Psi.toFixed(3)}`;
                cellsDataList.appendChild(listItem);
            });
        } catch (error) {
            console.error('Error fetching cells:', error);
        }
    };

    // SSE for real-time organism state
    const eventSource = new EventSource('/api/organism/stream');

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        tickSpan.textContent = data.tick;
        psiSpan.textContent = data.ψ.toFixed(3);
        cellsSpan.textContent = data.cells;
        fetchCells(); // Update cell list on each tick
    };

    eventSource.onerror = (error) => {
        console.error('EventSource failed:', error);
        eventSource.close();
    };

    // Procreate button functionality
    procreateButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/cell/procreate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ energy: 1.0 }), // Default energy for new cell
            });
            const result = await response.json();
            console.log('Procreate result:', result);
            fetchCells(); // Refresh cell list after procreation
        } catch (error) {
            console.error('Error procreating cell:', error);
        }
    });

    // Initial fetch of cells when the page loads
    fetchCells();
});
