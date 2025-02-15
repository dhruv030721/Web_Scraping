const fs = require('fs');
const axios = require('axios');

// Function to read JSON data
function readJson() {
    try {
        const data = fs.readFileSync('./links.json', 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Error reading JSON file:', error);
        return null;
    }
}

// Function to send a POST request
async function sendPostRequest(url) {
    try {
        const response = await axios.post("http://37.27.81.8:9010/scrape", { url }); // Replace with your payload
        console.log(`POST request to ${url} successful:`, response.status);
    } catch (error) {
        console.error(`Error sending POST request to ${url}:`, error.message);
    }
}

// Function to process links one by one
async function processLinksSequentially() {
    const links = readJson();
    if (!links['product_links'] || !Array.isArray(links['product_links'])) {
        console.error('Invalid JSON data. Expected an array of links.');
        return;
    }

    for (const link of links['product_links']) {
        console.log(`Sending POST request to: ${link}`);
        await sendPostRequest(link); // Wait for current request to complete before moving to next
        console.log(`Completed request for: ${link}\n`);
    }
}

// Start processing
processLinksSequentially();
