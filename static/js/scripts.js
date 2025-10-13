$(document).ready(function() {
    // Initialize Select2
    $('.select2').select2({
        theme: 'bootstrap-5',
        width: '100%'
    });

    // Initialize Select2 for modal
    $('#personalizedModal, #generateLinkModal, #bulkPersonalizedModal').on('shown.bs.modal', function () {
        $('.select2-modal').select2({
            theme: 'bootstrap-5',
            width: '100%',
            dropdownParent: $(this)
        });
    });

    // Clear bulk modal on close
    $('#bulkPersonalizedModal').on('hidden.bs.modal', function () {
        $('#bulkPersonalizedForm')[0].reset();
        $('#csvPreviewSection').hide();
        $('#csvPreviewBody').empty();
        csvData = [];
        $('#sendBulkInviteBtn').prop('disabled', true);
        $('#bulkCsvFile').val('');
    });

    // CSV File Upload Handler
    let csvData = [];
    $('#bulkCsvFile').on('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) {
                Swal.fire('Error', 'File size exceeds 5MB limit', 'error');
                $(this).val('');
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                const text = e.target.result;
                parseCSV(text);
            };
            reader.readAsText(file);
        }
    });

    // Parse CSV and show preview
    function parseCSV(text) {
        const lines = text.split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        csvData = [];
        
        const validTicketTypes = ticketTypes.map(t => t.value);
        let validCount = 0;
        let invalidCount = 0;

        $('#csvPreviewBody').empty();

        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;

            const values = lines[i].split(',').map(v => v.trim());
            const row = {
                index: i,
                name: values[0] || '',
                email: values[1] || '',
                ticketType: values[2] ? values[2].toLowerCase() : '',
                company: values[3] || '',
                message: values[4] || ''
            };

            csvData.push(row);
            addPreviewRow(row, validTicketTypes);
        }

        updateValidationCounts();
    }

    // Add preview row with editable ticket type and delete button
    function addPreviewRow(row, validTicketTypes) {
        const hasValidTicketType = validTicketTypes.includes(row.ticketType);
        const hasValidEmail = row.email && validateEmail(row.email);
        const isValid = row.name && hasValidEmail && hasValidTicketType;

        const statusBadge = isValid 
            ? '<span class="badge bg-success">Valid</span>' 
            : '<span class="badge bg-danger">Invalid</span>';

        const ticketTypeSelect = `
            <select class="form-select form-select-sm ticket-type-select" data-index="${row.index}" style="font-size: 11px; border: 1px solid #ced4da; padding: 4px 8px; background-color: white;">
                <option value="">Select Type</option>
                ${ticketTypes.map(t => `<option value="${t.value}" ${row.ticketType === t.value ? 'selected' : ''}>${t.display}</option>`).join('')}
            </select>
        `;

        const nameInput = `<input type="text" class="form-control form-control-sm editable-field" data-index="${row.index}" data-field="name" value="${row.name}" style="font-size: 11px; border: 1px solid #ced4da; padding: 4px 8px;">`;
        const emailInput = `<input type="email" class="form-control form-control-sm editable-field" data-index="${row.index}" data-field="email" value="${row.email}" style="font-size: 11px; border: 1px solid #ced4da; padding: 4px 8px;">`;
        const companyInput = `<input type="text" class="form-control form-control-sm editable-field" data-index="${row.index}" data-field="company" value="${row.company}" style="font-size: 11px; border: 1px solid #ced4da; padding: 4px 8px;">`;

        const deleteBtn = `
            <button class="btn btn-sm btn-danger delete-row-btn" data-index="${row.index}" style="font-size: 10px; padding: 2px 6px;">
                <i class="fas fa-trash"></i>
            </button>
        `;

        $('#csvPreviewBody').append(`
            <tr data-index="${row.index}" class="${isValid ? '' : 'table-danger'}">
                <td>${row.index}</td>
                <td>${nameInput}</td>
                <td>${emailInput}</td>
                <td>${ticketTypeSelect}</td>
                <td>${companyInput}</td>
                <td>${statusBadge}</td>
                <td class="text-center">${deleteBtn}</td>
            </tr>
        `);
    }

    // Update validation counts
    function updateValidationCounts() {
        const validTicketTypes = ticketTypes.map(t => t.value);
        let validCount = 0;
        let invalidCount = 0;

        csvData.forEach(row => {
            const hasValidTicketType = validTicketTypes.includes(row.ticketType);
            const hasValidEmail = row.email && validateEmail(row.email);
            const isValid = row.name && hasValidEmail && hasValidTicketType;
            
            if (isValid) validCount++;
            else invalidCount++;
        });

        $('#csvPreviewSection').show();
        $('#validRowsCount').text(`${validCount} Valid`);
        $('#invalidRowsCount').text(`${invalidCount} Invalid`);
        $('#totalRowsCount').text(`${csvData.length} Total`);

        if (validCount > 0) {
            $('#sendBulkInviteBtn').prop('disabled', false);
        } else {
            $('#sendBulkInviteBtn').prop('disabled', true);
        }
    }

    // Handle ticket type change
    $(document).on('change', '.ticket-type-select', function() {
        const index = $(this).data('index');
        const newTicketType = $(this).val();
        
        const rowData = csvData.find(r => r.index === index);
        if (rowData) {
            rowData.ticketType = newTicketType;
        }

        validateAndUpdateRow(index);
    });

    // Handle editable field changes
    $(document).on('blur', '.editable-field', function() {
        const index = $(this).data('index');
        const field = $(this).data('field');
        const value = $(this).val().trim();
        
        const rowData = csvData.find(r => r.index === index);
        if (rowData) {
            rowData[field] = value;
        }

        validateAndUpdateRow(index);
    });

    // Validate and update row appearance
    function validateAndUpdateRow(index) {
        const rowData = csvData.find(r => r.index === index);
        if (!rowData) return;

        const validTicketTypes = ticketTypes.map(t => t.value);
        const hasValidTicketType = validTicketTypes.includes(rowData.ticketType);
        const hasValidEmail = rowData.email && validateEmail(rowData.email);
        const isValid = rowData.name && hasValidEmail && hasValidTicketType;

        const $row = $(`tr[data-index="${index}"]`);
        if (isValid) {
            $row.removeClass('table-danger');
            $row.find('td:eq(5)').html('<span class="badge bg-success">Valid</span>');
        } else {
            $row.addClass('table-danger');
            $row.find('td:eq(5)').html('<span class="badge bg-danger">Invalid</span>');
        }

        updateValidationCounts();
    }

    // Handle row deletion
    $(document).on('click', '.delete-row-btn', function() {
        const index = $(this).data('index');
        
        csvData = csvData.filter(r => r.index !== index);
        $(`tr[data-index="${index}"]`).remove();
        
        updateValidationCounts();

        if (csvData.length === 0) {
            $('#csvPreviewSection').hide();
            $('#sendBulkInviteBtn').prop('disabled', true);
        }
    });

    // Clear all preview
    $('#clearPreviewBtn').on('click', function() {
        Swal.fire({
            icon: 'warning',
            title: 'Clear All Data?',
            text: 'This will remove all uploaded data. Are you sure?',
            showCancelButton: true,
            confirmButtonText: 'Yes, Clear All',
            confirmButtonColor: '#d33'
        }).then((result) => {
            if (result.isConfirmed) {
                csvData = [];
                $('#csvPreviewBody').empty();
                $('#csvPreviewSection').hide();
                $('#sendBulkInviteBtn').prop('disabled', true);
                $('#bulkCsvFile').val('');
            }
        });
    });

    // Add manual row
    $(document).on('click', '#addManualRowBtn', function() {
        if (!$('#csvPreviewSection').is(':visible')) {
            $('#csvPreviewSection').show();
        }

        const newIndex = csvData.length > 0 ? Math.max(...csvData.map(r => r.index)) + 1 : 1;

        const newRow = {
            index: newIndex,
            name: '',
            email: '',
            ticketType: '',
            company: '',
            message: ''
        };

        csvData.push(newRow);

        const validTicketTypes = ticketTypes.map(t => t.value);
        addPreviewRow(newRow, validTicketTypes);

        updateValidationCounts();

        setTimeout(() => {
            const $newRow = $(`tr[data-index="${newIndex}"]`);
            if ($newRow.length) {
                $newRow[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                $newRow.find('.editable-field[data-field="name"]').focus();
            }
        }, 100);

        Swal.fire({
            icon: 'success',
            title: 'Row Added',
            text: 'Fill in the details for the new recipient',
            timer: 1500,
            showConfirmButton: false
        });
    });

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Download CSV Template
    $('#downloadTemplateBtn').on('click', function() {
        const csvContent = `Full Name,Email,Ticket Type,Company Name,Personal Message\nJohn Doe,john@example.com,${ticketTypes[0].value},ABC Corp,Looking forward to seeing you\nJane Smith,jane@example.com,${ticketTypes[1].value},XYZ Inc,`;
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'bulk_invitation_template.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    });

    // Initialize DataTable with AJAX
    const table = $('#invitationTable').DataTable({
        pageLength: 10,
        responsive: true,
        order: [[1, 'desc']],
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip',
        language: {
            lengthMenu: "Show _MENU_ entries",
            search: "Search:",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            paginate: {
                first: "First",
                last: "Last",
                next: "Next",
                previous: "Previous"
            }
        },
        columnDefs: [
            { orderable: false, targets: [0, 9] },
            { className: 'text-center', targets: [0] }
        ],
        ajax: {
            url: '{% url "invitation_list" %}',
            dataSrc: ''
        },
        columns: [
            {
                data: null,
                render: function(data, type, row, meta) {
                    return `<input type="checkbox" class="table-checkbox row-checkbox" data-id="${row.id}">`;
                }
            },
            { data: 'title_or_name' },
            { data: 'email' },
            { 
                data: 'invite_type',
                render: function(data) {
                    const type = ticketTypes.find(t => t.value === data);
                    return type ? type.display : data;
                }
            },
            { data: 'expiry_date' },
            { data: 'link_limit' },
            { data: 'registered_count' },
            { 
                data: 'invitation_key',
                render: function(data) {
                    return data ? `<button class="btn btn-sm btn-primary copy-link" data-link="${data}"><i class="fas fa-copy me-1"></i>Copy Link</button>` : '';
                }
            },
            {
                data: 'status',
                render: function(data) {
                    const status = invitationStatuses.find(s => s.value === data);
                    const statusClass = data === 'active' ? 'success' : data === 'expired' ? 'danger' : 'secondary';
                    return `<span class="badge bg-${statusClass}">${status ? status.display : data}</span>`;
                }
            },
            {
                data: null,
                render: function(data, type, row) {
                    return `
                        <button class="btn btn-action btn-sm btn-info" title="View" data-id="${row.id}"><i class="fas fa-eye"></i></button>
                        <button class="btn btn-action btn-sm btn-warning" title="Edit" data-id="${row.id}"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-action btn-sm btn-success" title="Broadcast" data-id="${row.id}"><i class="fas fa-broadcast-tower"></i></button>
                        <button class="btn btn-action btn-sm btn-danger" title="Delete" data-id="${row.id}"><i class="fas fa-trash"></i></button>
                    `;
                }
            }
        ],
        initComplete: function() {
            $('.dataTables_length select').addClass('form-select form-select-sm').css({
                'width': 'auto',
                'display': 'inline-block',
                'margin': '0 8px'
            });
            $('.dataTables_filter input').addClass('form-control form-control-sm').css({
                'width': 'auto',
                'display': 'inline-block',
                'margin-left': '8px'
            });
        }
    });

    // Checkbox Selection Logic
    let selectedRows = new Set();

    $('#selectAll').on('change', function() {
        const isChecked = $(this).prop('checked');
        $('.row-checkbox').prop('checked', isChecked);
        
        if (isChecked) {
            $('.row-checkbox').each(function() {
                selectedRows.add($(this).data('id'));
                $(this).closest('tr').addClass('selected');
            });
        } else {
            selectedRows.clear();
            $('tbody tr').removeClass('selected');
        }
        updateBulkActionsBar();
    });

    $(document).on('change', '.row-checkbox', function() {
        const rowId = $(this).data('id');
        const isChecked = $(this).prop('checked');
        
        if (isChecked) {
            selectedRows.add(rowId);
            $(this).closest('tr').addClass('selected');
        } else {
            selectedRows.delete(rowId);
            $(this).closest('tr').removeClass('selected');
        }
        
        const totalCheckboxes = $('.row-checkbox').length;
        const checkedCheckboxes = $('.row-checkbox:checked').length;
        $('#selectAll').prop('checked', totalCheckboxes === checkedCheckboxes);
        $('#selectAll').prop('indeterminate', checkedCheckboxes > 0 && checkedCheckboxes < totalCheckboxes);
        
        updateBulkActionsBar();
    });

    function updateBulkActionsBar() {
        const count = selectedRows.size;
        if (count > 0) {
            $('#bulkActionsBar').addClass('show');
            $('#selectedCount').text(count);
        } else {
            $('#bulkActionsBar').removeClass('show');
        }
    }

    $('#clearSelectionBtn').click(function() {
        selectedRows.clear();
        $('.row-checkbox, #selectAll').prop('checked', false);
        $('tbody tr').removeClass('selected');
        updateBulkActionsBar();
    });

    $('#bulkSendBtn').click(function() {
        Swal.fire({
            icon: 'info',
            title: 'Send Invitations',
            text: `Send invitations to ${selectedRows.size} selected items?`,
            showCancelButton: true,
            confirmButtonText: 'Send All'
        }).then((result) => {
            if (result.isConfirmed) {
                showLoading();
                setTimeout(() => {
                    hideLoading();
                    Swal.fire('Sent!', `${selectedRows.size} invitations have been sent.`, 'success');
                    $('#clearSelectionBtn').click();
                }, 1500);
            }
        });
    });

    $('#bulkActivateBtn').click(function() {
        Swal.fire({
            icon: 'question',
            title: 'Activate Selected',
            text: `Activate ${selectedRows.size} selected items?`,
            showCancelButton: true,
            confirmButtonText: 'Activate'
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire('Activated!', `${selectedRows.size} items have been activated.`, 'success');
                $('#clearSelectionBtn').click();
            }
        });
    });

    $('#bulkDeactivateBtn').click(function() {
        Swal.fire({
            icon: 'warning',
            title: 'Deactivate Selected',
            text: `Deactivate ${selectedRows.size} selected items?`,
            showCancelButton: true,
            confirmButtonText: 'Deactivate'
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire('Deactivated!', `${selectedRows.size} items have been deactivated.`, 'success');
                $('#clearSelectionBtn').click();
            }
        });
    });

    $('#bulkExportBtn').click(function() {
        showLoading();
        setTimeout(() => {
            hideLoading();
            Swal.fire('Exported!', `${selectedRows.size} items have been exported to Excel.`, 'success');
        }, 1000);
    });

    $('#bulkDeleteBtn').click(function() {
        Swal.fire({
            icon: 'error',
            title: 'Delete Selected',
            text: `Are you sure you want to delete ${selectedRows.size} selected items?`,
            showCancelButton: true,
            confirmButtonColor: '#d33',
            confirmButtonText: 'Delete All'
        }).then((result) => {
            if (result.isConfirmed) {
                showLoading();
                setTimeout(() => {
                    hideLoading();
                    Swal.fire('Deleted!', `${selectedRows.size} items have been deleted.`, 'success');
                    selectedRows.forEach(rowId => {
                        table.row($(`tr:has(input[data-id="${rowId}"])`)).remove();
                    });
                    table.draw();
                    $('#clearSelectionBtn').click();
                }, 1000);
            }
        });
    });

    $(document).on('click', '.copy-link', function() {
        const link = $(this).data('link');
        navigator.clipboard.writeText(link);
        const btn = $(this);
        const originalHtml = btn.html();
        btn.html('<i class="fas fa-check me-1"></i>Copied!').addClass('btn-success').removeClass('btn-primary');
        setTimeout(() => {
            btn.html(originalHtml).addClass('btn-primary').removeClass('btn-success');
        }, 2000);
    });

    $('#searchBtn').click(function() {
        showLoading();
        setTimeout(() => {
            const keyword = $('#searchKeyword').val();
            table.search(keyword).draw();
            hideLoading();
            Swal.fire({
                icon: 'success',
                title: 'Search Complete',
                text: `Found ${table.page.info().recordsDisplay} results`,
                timer: 1500,
                showConfirmButton: false
            });
        }, 500);
    });

    $('#resetBtn').click(function() {
        $('#searchKeyword').val('');
        $('#filterStatus').val('').trigger('change');
        $('#filterType').val('').trigger('change');
        $('#filterDate').val('');
        table.search('').draw();
    });

    $('#exportBtn').click(function() {
        Swal.fire({
            title: 'Export Data',
            text: 'Select export format',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Excel',
            cancelButtonText: 'CSV',
            showDenyButton: true,
            denyButtonText: 'PDF'
        }).then((result) => {
            if (result.isConfirmed || result.isDenied || result.dismiss === Swal.DismissReason.cancel) {
                showLoading();
                setTimeout(() => {
                    hideLoading();
                    Swal.fire('Exported!', 'Your file has been downloaded.', 'success');
                }, 1000);
            }
        });
    });

    $('#submitLinkBtn').click(function() {
        if ($('#generateLinkForm')[0].checkValidity()) {
            $('#generateLinkForm').submit();
        } else {
            $('#generateLinkForm')[0].reportValidity();
        }
    });

    $('#sendInviteBtn').click(function() {
        if ($('#personalizedForm')[0].checkValidity()) {
            $('#personalizedForm').submit();
        } else {
            $('#personalizedForm')[0].reportValidity();
        }
    });

    $('#sendBulkInviteBtn').click(function() {
        if ($('#bulkPersonalizedForm')[0].checkValidity()) {
            $('#bulkPersonalizedForm').submit();
        } else {
            $('#bulkPersonalizedForm')[0].reportValidity();
        }
    });

    $(document).on('click', '.btn-action', function() {
        const action = $(this).attr('title');
        const rowId = $(this).data('id');
        
        switch(action) {
            case 'View':
                Swal.fire('View Details', `Viewing details for invitation ID: ${rowId}`, 'info');
                break;
            case 'Edit':
                Swal.fire('Edit Record', `Editing invitation ID: ${rowId}`, 'info');
                break;
            case 'Broadcast':
                Swal.fire('Broadcast', 'Broadcasting invitation link...', 'info');
                break;
            case 'Delete':
                Swal.fire({
                    title: 'Are you sure?',
                    text: "You won't be able to revert this!",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonText: 'Cancel',
                    confirmButtonText: 'Yes, delete it!'
                }).then((result) => {
                    if (result.isConfirmed) {
                        Swal.fire('Deleted!', 'The invitation has been deleted.', 'success');
                    }
                });
                break;
        }
    });

    function showLoading() {
        $('#loadingOverlay').addClass('show');
    }

    function hideLoading() {
        $('#loadingOverlay').removeClass('show');
    }

    $('.stat-value').each(function() {
        const $this = $(this);
        const countTo = $this.attr('data-count');
        $({ countNum: 0 }).animate({
            countNum: countTo
        }, {
            duration: 1500,
            easing: 'swing',
            step: function() {
                $this.text(Math.floor(this.countNum));
            },
            complete: function() {
                $this.text(this.countNum);
            }
        });
    });

    $('[title]').tooltip();

    const today = new Date();
    const futureDate = new Date(today.setMonth(today.getMonth() + 1));
    $('#expireDate, #personalExpireDate, #bulkExpireDate').val(futureDate.toISOString().split('T')[0]);
});