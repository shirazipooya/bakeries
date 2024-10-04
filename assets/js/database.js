document.addEventListener('DOMContentLoaded', function () {

    let selectedRowId;

    // Delete Functionality
    document.querySelectorAll('.deleteBtn').forEach(button => {
        button.addEventListener('click', function () {
            selectedRowId = this.closest('tr').getAttribute('data-id');
            console.log(selectedRowId);
            
        });
    });

    document.getElementById('confirmDelete').addEventListener('click', function () {
        fetch(`/delete_record/${selectedRowId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                location.reload();  // Reload the page after deleting
            }
        });
    });

});
