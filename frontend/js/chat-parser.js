/**
 * Chart Parser for FinSight
 * Parses and displays base64-encoded images from agent responses
 */

class ChartParser {
    constructor() {
        this.imagePattern = /\[IMAGE_DATA\](data:image\/png;base64,[^\[]+)\[\/IMAGE_DATA\]/g;
        this.markdownImagePattern = /!\[.*?\]\((data:image\/png;base64,[^)]+)\)/g;
    }

    /**
     * Extract images from response text
     * @param {string} text - The response text
     * @returns {Object} - { text: cleanedText, images: [imageData] }
     */
    parseResponse(text) {
        const images = [];
        let cleanText = text;

        // Extract [IMAGE_DATA]...[/IMAGE_DATA] format
        let match;
        while ((match = this.imagePattern.exec(text)) !== null) {
            images.push(match[1]);
            cleanText = cleanText.replace(match[0], '');
        }

        // Extract markdown format ![...](data:image...)
        this.imagePattern.lastIndex = 0; // Reset regex
        while ((match = this.markdownImagePattern.exec(text)) !== null) {
            images.push(match[1]);
            cleanText = cleanText.replace(match[0], '');
        }

        // Clean up any leftover markers
        cleanText = cleanText
            .replace(/\[IMAGE_DATA\]/g, '')
            .replace(/\[\/IMAGE_DATA\]/g, '')
            .trim();

        return {
            text: cleanText,
            images: images
        };
    }

    /**
     * Create chart element
     * @param {string} imageData - Base64 image data
     * @returns {HTMLElement} - Chart container element
     */
    createChartElement(imageData) {
        const container = document.createElement('div');
        container.className = 'chart-container';

        const img = document.createElement('img');
        img.src = imageData;
        img.alt = 'Stock Chart';
        img.loading = 'lazy';

        // Add download button
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'chart-download-btn';
        downloadBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 2V10M8 10L5 7M8 10L11 7M2 12V13C2 13.5304 2.21071 14.0391 2.58579 14.4142C2.96086 14.7893 3.46957 15 4 15H12C12.5304 15 13.0391 14.7893 13.4142 14.4142C13.7893 14.0391 14 13.5304 14 13V12" 
                    stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Download Chart
        `;
        downloadBtn.onclick = () => this.downloadChart(imageData);

        container.appendChild(img);
        container.appendChild(downloadBtn);

        return container;
    }

    /**
     * Download chart as PNG
     * @param {string} imageData - Base64 image data
     */
    downloadChart(imageData) {
        const link = document.createElement('a');
        link.href = imageData;
        link.download = `finsight-chart-${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * Format text with markdown-like styling
     * @param {string} text - Plain text
     * @returns {string} - HTML formatted text
     */
    formatText(text) {
        // Convert markdown tables to HTML
        if (text.includes('|')) {
            text = this.convertMarkdownTable(text);
        }

        // Bold text: **text** or __text__
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');

        // Italic text: *text* or _text_
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/_(.*?)_/g, '<em>$1</em>');

        // Inline code: `code`
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Bullet points
        text = text.replace(/^[•\-\*]\s+(.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // Line breaks
        text = text.replace(/\n\n/g, '</p><p>');
        text = text.replace(/\n/g, '<br>');

        return `<p>${text}</p>`;
    }

    /**
     * Convert markdown table to HTML
     * @param {string} text - Text containing markdown table
     * @returns {string} - HTML formatted text
     */
    convertMarkdownTable(text) {
        const lines = text.split('\n');
        let tableHTML = '';
        let inTable = false;
        let processedLines = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();

            if (line.startsWith('|') && line.endsWith('|')) {
                if (!inTable) {
                    tableHTML = '<div class="table-wrapper"><table>';
                    inTable = true;
                }

                const cells = line.split('|').filter(cell => cell.trim());
                
                // Check if this is a separator line (|---|---|)
                if (cells.every(cell => cell.match(/^[\s\-:]+$/))) {
                    continue;
                }

                // Determine if this is a header row (first row)
                const isHeader = i === 0 || (i === 1 && lines[i-1].includes('|'));
                const tag = isHeader ? 'th' : 'td';

                tableHTML += '<tr>';
                cells.forEach(cell => {
                    tableHTML += `<${tag}>${cell.trim()}</${tag}>`;
                });
                tableHTML += '</tr>';

            } else {
                if (inTable) {
                    tableHTML += '</table></div>';
                    processedLines.push(tableHTML);
                    tableHTML = '';
                    inTable = false;
                }
                processedLines.push(line);
            }
        }

        if (inTable) {
            tableHTML += '</table></div>';
            processedLines.push(tableHTML);
        }

        return processedLines.join('\n');
    }
}

// Export for use in main app
window.ChartParser = ChartParser;