document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('grant-form');
    if (!form) return;
    const submitButton = document.getElementById('submit-btn');
    const inputCard = document.getElementById('input-card');
    const loadingContainer = document.getElementById('loading-container');
    const resultContainer = document.getElementById('result-container');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const orgType = document.getElementById('org_type').value;
        const mission = document.getElementById('mission').value;

        // 1. Switch to Loading State
        inputCard.style.display = 'none';
        loadingContainer.style.display = 'block';
        
        try {
            const loadingHtml = await fetch('/loading-fragment').then(res => res.text());
            loadingContainer.innerHTML = loadingHtml;
        } catch (err) {
            loadingContainer.innerHTML = '<div class="card"><h3>Loading...</h3></div>';
        }

        // 2. Call Backend
        try {
            const response = await fetch('/run-grant-writer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ org_type: orgType, mission: mission })
            });

            if (!response.ok) {
                const contentType = response.headers.get('content-type') || '';
                let message = `Request failed (${response.status}). Please try again.`;
                if (contentType.includes('application/json')) {
                    const errData = await response.json();
                    message = [errData.error, errData.details].filter(Boolean).join(' ');
                }
                throw new Error(message);
            }

            // 3. Render Result
            const resultHtml = await response.text();
            loadingContainer.style.display = 'none';
            resultContainer.innerHTML = resultHtml;
            resultContainer.style.display = 'block';

            // =========================================================
            //  CLEAN UP TEXT (Remove Logs)
            // =========================================================
            const rawTextArea = document.getElementById('raw-data');
            const markdownOutputDiv = document.getElementById('markdown-output');
            
            if (rawTextArea && markdownOutputDiv) {
                let rawText = rawTextArea.value;

                // A. Split text at the "FINAL GRANT REPORT" banner
                const splitMarker = "FINAL GRANT REPORT";
                if (rawText.includes(splitMarker)) {
                    rawText = rawText.split(splitMarker)[1];
                }

                // B. Remove the trailing "[Success]" message
                const successMarker = "[Success] Report saved to";
                if (rawText.includes(successMarker)) {
                    rawText = rawText.split(successMarker)[0];
                }

                // C. Clean up hashes and whitespace
                rawText = rawText.replace(/^[#=\s]+$/gm, "").trim();

                // D. Render Clean Markdown
                const renderedMarkdown = marked.parse(rawText);
                markdownOutputDiv.innerHTML = window.DOMPurify
                    ? DOMPurify.sanitize(renderedMarkdown)
                    : document.createTextNode(rawText).textContent;
            }

        } catch (error) {
            loadingContainer.style.display = 'none';
            inputCard.style.display = 'block';
            alert(`Error: ${error.message || 'Unexpected error. Please try again.'}`);
        }
    });
});