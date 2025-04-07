document.addEventListener('DOMContentLoaded', function() {
    const submitBtn = document.getElementById('submit-btn');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    
    submitBtn.addEventListener('click', function() {
        // Get input values
        const name = document.getElementById('name').value || 'User';
        const query = document.getElementById('query').value;
        
        if (!query) {
            alert('Please enter a research question');
            return;
        }
        
        // Show loading, hide results
        loadingDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        
        // Make API request
        fetch('/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, query })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading
            loadingDiv.classList.add('hidden');
            
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }
            
            // Update results
            document.getElementById('topic-title').textContent = data.topic;
            document.getElementById('summary').textContent = data.summary;
            
            const sourcesList = document.getElementById('sources-list');
            sourcesList.innerHTML = '';
            data.sources.forEach(source => {
                const li = document.createElement('li');
                li.textContent = source;
                sourcesList.appendChild(li);
            });
            
            // Set PDF download link with proper attributes
            const pdfLink = document.getElementById('pdf-download');
            if (data.pdf_path) {
                pdfLink.setAttribute('href', data.pdf_path);
                pdfLink.setAttribute('download', '');
                pdfLink.style.display = 'inline-block';
            } else {
                pdfLink.style.display = 'none';
            }
    
            // Add text file download as fallback
            const txtLink = document.getElementById('txt-download');
            if (txtLink && data.txt_path) {
                txtLink.setAttribute('href', data.txt_path);
                txtLink.setAttribute('download', '');
                txtLink.style.display = 'inline-block';
            }
            
            // Show results
            resultsDiv.classList.remove('hidden');
        })
        .catch(error => {
            loadingDiv.classList.add('hidden');
            alert('Error: ' + error);
        });
    });
});