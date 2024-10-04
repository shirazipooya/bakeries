document.addEventListener('DOMContentLoaded', function () {
    let selectedRowId;

    // Pagination variables
    let currentPage = 1;
    const rowsPerPage = 15; // Number of rows per page
    const recordsTable = document.getElementById('recordsTable');
    const rows = recordsTable.querySelectorAll('tr');
    const totalPages = Math.ceil(rows.length / rowsPerPage);

    // Function to display the rows for the current page
    function displayRows() {
        // Hide all rows initially
        rows.forEach((row, index) => {
            row.style.display = 'none';
        });

        // Show only the rows for the current page
        const start = (currentPage - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        rows.forEach((row, index) => {
            if (index >= start && index < end) {
                row.style.display = '';
            }
        });

        // Update pagination controls
        document.getElementById('prevPage').disabled = currentPage === 1;
        document.getElementById('nextPage').disabled = currentPage === totalPages;

        // Update page numbers display
        updatePageNumbers();
    }

    // Function to update page numbers display
    function updatePageNumbers() {
        const pageNumbers = document.getElementById('pageNumbers');
        pageNumbers.innerHTML = `صفحه   ${currentPage}   از   ${totalPages}`;
    }

    // Event listeners for pagination controls
    document.getElementById('prevPage').addEventListener('click', function () {
        if (currentPage > 1) {
            currentPage--;
            displayRows();
        }
    });

    document.getElementById('nextPage').addEventListener('click', function () {
        if (currentPage < totalPages) {
            currentPage++;
            displayRows();
        }
    });

    // Initial table display (first page)
    displayRows();
});