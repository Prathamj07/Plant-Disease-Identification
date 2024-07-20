document.addEventListener("DOMContentLoaded", function() {
    const uploadForm = document.getElementById('uploadForm');

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData();
            const image = document.getElementById('image').files[0];
            formData.append('image', image);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const uploadResult = document.getElementById('uploadResult');
                uploadResult.innerHTML = `Predicted plant disease: ${data.predicted_class}, Confidence: ${data.confidence}`;
            })
            .catch(error => console.error('Error:', error));
        });
    }
});
document.getElementById('show-register').addEventListener('click', function() {
    document.getElementById('login-container').classList.add('hidden');
    document.getElementById('register-container').classList.remove('hidden');
});

document.getElementById('show-login').addEventListener('click', function() {
    document.getElementById('register-container').classList.add('hidden');
    document.getElementById('login-container').classList.remove('hidden');
});


