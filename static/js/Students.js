
    // let html5QrcodeScanner;

    // // Function to handle successful QR code scan
    // function handleScanSuccess(qrCodeMessage) {
    //     const textarea = document.getElementById('attendanceInput');
    //     let existingData = textarea.value.split(',').map(item => item.trim()).filter(item => item);

    //     // Check if the scanned QR code message is already present
    //     if (!existingData.includes(qrCodeMessage)) {
    //         existingData.push(qrCodeMessage);
    //         textarea.value = existingData.join(', ') + ', ';
    //     }
    // }

    // // Function to handle errors
    // function handleScanError(err) {
    //     console.error(err);
    // }

    // // Event listener for modal show to start the QR code scanner
    // $('#qrModal').on('shown.bs.modal', function () {
    //     html5QrcodeScanner = new Html5QrcodeScanner('reader', {
    //         qrbox: {
    //             width: 250,
    //             height: 250,
    //         },
    //         fps: 20,
    //     });
    //     html5QrcodeScanner.render(handleScanSuccess, handleScanError);
    // });

    // // Event listener for modal hide to clear the QR code scanner
    // $('#qrModal').on('hidden.bs.modal', function () {
    //     html5QrcodeScanner.clear();
    //     const readerElement = document.getElementById('reader');
    //     while (readerElement.firstChild) {
    //         readerElement.removeChild(readerElement.firstChild);
    //     }
    // });
