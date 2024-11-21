function changeOrder(button) {
    // Logic to change the order status
    const row = button.parentElement.parentElement; 
    const statusSelect = row.querySelector('select'); 
    const selectedStatus = statusSelect.value; 
    alert('Order status changed to: ' + selectedStatus);

}

function deleteOrder(button, orderId) {
    // Find the row that contains the delete button
    var row = button.closest('tr');
   
    // Optionally, add a confirmation step before deleting
    if (confirm("Are you sure you want to remove this order from the view?")) {
        // Temporarily remove the row from the table (without removing from the database)
        row.style.display = 'none';

        // Send an AJAX request to mark the order as removed in the database
        fetch(`/remove_order/${orderId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Order marked as removed.");
            } else {
                alert("Failed to mark order as removed.");
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

function deleteOrder(orderId) {
    if (confirm('Are you sure you want to delete this order?')) {
        fetch('/delete_order/' + orderId, {
            method: 'DELETE'
        }).then(response => {
            if (response.ok) {
                document.getElementById("order_" + orderId).remove(); 
            } else {
                alert('Failed to delete order.');
            }
        });
    }
}

function showEditDialog(orderId) {
    const row = document.getElementById(`order_${orderId}`);
    
    // Set hidden orderId value
    document.getElementById("orderId").value = orderId;
    
    // Populate the text fields
    document.getElementById("customerName").value = row.cells[0].innerText;
    document.getElementById("contactNumber").value = row.cells[1].innerText;
    document.getElementById("address").value = row.cells[2].innerText;
    document.getElementById("pickupPlace").value = row.cells[3].innerText;
    document.getElementById("pickupDate").value = row.cells[4].innerText;
    document.getElementById("delicacy").value = row.cells[5].innerText;
    document.getElementById("quantity").value = row.cells[6].innerText;
    document.getElementById("container").value = row.cells[7].innerText;
    document.getElementById("specialRequest").value = row.cells[8].innerText;

    // Get the status value and log it for debugging
    const status = row.cells[9].innerText.trim(); 
    console.log('Retrieved status:', status); 
    
    // Extract the actual status (IN_PROGRESS) from the string "OrderStatus.IN_PROGRESS"
    const statusValue = status.split('.')[1]; 
    console.log('Extracted status value:', statusValue); 

    // Get the status dropdown and log its options
    const statusDropdown = document.getElementById("status");
    Array.from(statusDropdown.options).forEach(option => {
        console.log('Option value:', option.value); 
    });

    // Set the selected option based on the extracted status
    Array.from(statusDropdown.options).forEach(option => {
        if (option.value === statusValue) {
            option.selected = true; 
        }
    });

    // Attach the orderId to the save button
    document.getElementById("saveButton").setAttribute("data-order-id", orderId);
    
    // Display the modal
    document.getElementById("editModal").style.display = "block";
    document.getElementById("modalOverlay").style.display = "block";
}


function saveOrder() {
    const orderId = document.getElementById("orderId").value;
    const row = document.getElementById(`order_${orderId}`);
    row.cells[0].innerText = document.getElementById("customerName").value;
    row.cells[1].innerText = document.getElementById("contactNumber").value;
    row.cells[2].innerText = document.getElementById("address").value;
    row.cells[3].innerText = document.getElementById("pickupPlace").value;
    row.cells[4].innerText = document.getElementById("pickupDate").value;
    row.cells[5].innerText = document.getElementById("delicacy").value;
    row.cells[6].innerText = document.getElementById("quantity").value;
    row.cells[7].innerText = document.getElementById("container").value;
    row.cells[8].innerText = document.getElementById("specialRequest").value;
    row.cells[9].innerText = document.getElementById("status").value;
    closeModal();
}

function closeModal() {
    document.getElementById("editModal").style.display = "none";
    document.getElementById("modalOverlay").style.display = "none";
}

function saveOrder() {
    const orderId = document.getElementById("saveButton").getAttribute("data-order-id");
    console.log("Save button clicked! Order ID: " + orderId);

    let formData = {
        customer_name: document.getElementById("customerName").value,
        contact_number: document.getElementById("contactNumber").value,
        address: document.getElementById("address").value,
        pickup_place: document.getElementById("pickupPlace").value,
        pickup_date: document.getElementById("pickupDate").value,
        delicacy: document.getElementById("delicacy").value,
        quantity: document.getElementById("quantity").value,
        container: document.getElementById("container").value,
        special_request: document.getElementById("specialRequest").value,
        status: document.getElementById("status").value,
    };

    console.log('Form data being sent:', JSON.stringify(formData));

    fetch('/update_order/' + orderId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    })
    
    .then(response => {
        console.log('Response:', response);
        return response.json();
    })
    .then(data => {
        console.log('Data received from server:', data);
        if (data.success) {
            closeModal()
            handleSortChange()
        
        } else {
            alert('Failed to update order.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the order.');
    });
}

function updateUI(orderId, updatedOrder) {
    console.log(updatedOrder); 
    const updateTextContent = (elementId, newText) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerText = newText;
        } else {
            console.warn(`Element with ID ${elementId} not found`);
        }
    };

    updateTextContent("customer_name_" + orderId, updatedOrder.customer_name);
    updateTextContent("contact_number_" + orderId, updatedOrder.contact_number);
    updateTextContent("address_" + orderId, updatedOrder.address);
    updateTextContent("pickup_place_" + orderId, updatedOrder.pickup_place);
    updateTextContent("pickup_date_" + orderId, updatedOrder.pickup_date);
    updateTextContent("delicacy_" + orderId, updatedOrder.delicacy);
    updateTextContent("quantity_" + orderId, updatedOrder.quantity);
    updateTextContent("container_" + orderId, updatedOrder.container);
    updateTextContent("special_request_" + orderId, updatedOrder.special_request);
    updateTextContent("status_" + orderId, updatedOrder.status);
}


function createOrder() {
    const customerName = document.getElementById('customerName').value;
    const contactNumber = document.getElementById('contactNumber').value;
    const address = document.getElementById('address').value;
    const pickupPlace = document.getElementById('pickupPlace').value;
    const pickupDate = document.getElementById('pickupDate').value;
    const delicacy = document.getElementById('delicacy').value;
    const quantity = document.getElementById('quantity').value;
    const container = document.getElementById('container').value;
    const specialRequest = document.getElementById('specialRequest').value;

    // Sending data to backend using fetch (example)
    fetch('/create_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            customer_name: customerName,
            contact_number: contactNumber,
            address: address,
            pickup_place: pickupPlace,
            pickup_date: pickupDate,
            delicacy: delicacy,
            quantity: quantity,
            container: container,
            special_request: specialRequest
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Order created successfully');
            closeModal();  
        } else {
            alert('Error creating order');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while creating the order.');
    });
}

document.addEventListener("DOMContentLoaded", () => {
    // Define the mapping of statuses to their user-friendly names
    const statusMap = {
        "OrderStatus.PENDING": "Pending",
        "OrderStatus.IN_PROGRESS": "In Progress",
        "OrderStatus.COMPLETED": "Completed",
        "OrderStatus.REMOVED": "Removed",
    };

    // Select all rows in the table body
    const rows = document.querySelectorAll("#ordersTable tbody tr");

    // Loop through each row to update the status text
    rows.forEach(row => {
        const statusCell = row.cells[9]; 
        const currentStatus = statusCell.innerText.trim();

        // Replace the status if it exists in the mapping
        if (statusMap[currentStatus]) {
            statusCell.innerText = statusMap[currentStatus];
        }
    });
});