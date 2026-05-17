// Password toggle
function togglePassword(id) {
    const input = document.getElementById(id);
    const btn = input.parentElement.querySelector('.pw-toggle');
    if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '🙈';
    } else {
        input.type = 'password';
        btn.textContent = '👁️';
    }
}

// Password match check on signup
document.addEventListener('submit', function(e) {
    const form = e.target;
    const pw  = document.getElementById('signupPassword');
    const cpw = document.getElementById('confirmPassword');
    if (pw && cpw && pw.value !== cpw.value) {
        e.preventDefault();
        let err = document.getElementById('pw-error');
        if (!err) {
            err = document.createElement('div');
            err.id = 'pw-error';
            err.className = 'form-error';
            form.prepend(err);
        }
        err.textContent = '❌ Passwords do not match!';
    }
});

// Upload area label update
const fileInput = document.getElementById('video-input');
if (fileInput) {
    fileInput.addEventListener('change', function() {
        const label = document.getElementById('file-label');
        if (label && this.files[0]) {
            label.textContent = '📹 ' + this.files[0].name;
        }
    });
}

// Upload area drag-and-drop
const uploadArea = document.querySelector('.upload-area');
if (uploadArea) {
    uploadArea.addEventListener('dragover', e => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--accent)';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '';
    });
    uploadArea.addEventListener('drop', e => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        if (fileInput && e.dataTransfer.files[0]) {
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
    uploadArea.addEventListener('click', () => fileInput && fileInput.click());
}
