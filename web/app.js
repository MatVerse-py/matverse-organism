document.addEventListener('DOMContentLoaded', () => {
    // Determine the backend URL based on the environment
    const backendUrl = window.location.hostname === 'localhost' 
        ? 'http://localhost:8765' 
        : 'https://matverse-api.railway.app'; // Will be updated after Railway deployment

    const tickSpan = document.getElementById('tick');
    const psiSpan = document.getElementById('psi');
    const cellsSpan = document.getElementById('cells');
    const procreateButton = document.getElementById('procreate-button');
    const cellsDataList = document.getElementById('cells-data');

    // Function to fetch all cells
    const fetchCells = async () => {
        try {
            const response = await fetch(`${backendUrl}/api/cells`);
            const cells = await response.json();
            cellsDataList.innerHTML = ''; // Clear previous list
            cells.forEach(cell => {
                const listItem = document.createElement('li');
                listItem.textContent = `ID: ${cell.id}, Energy: ${cell.e.toFixed(3)}, Psi: ${cell.ψ.toFixed(3)}`;
                cellsDataList.appendChild(listItem);
            });
        } catch (error) {
            console.error('Error fetching cells:', error);
            cellsDataList.innerHTML = '<li style="color: red;">Error connecting to backend</li>';
        }
    };

    // SSE for real-time organism state
    const connectSSE = () => {
        const eventSource = new EventSource(`${backendUrl}/api/organism/stream`);

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
            // Attempt to reconnect after 5 seconds
            setTimeout(connectSSE, 5000);
        };
    };

    connectSSE();

    // Procreate button functionality
    procreateButton.addEventListener('click', async () => {
        try {
            const response = await fetch(`${backendUrl}/api/cell/procreate`, {
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
