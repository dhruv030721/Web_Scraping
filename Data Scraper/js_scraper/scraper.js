const puppeteer = require('puppeteer');
const express = require('express')
const fs = require('fs');
const morgan = require('morgan')
const axios = require('axios')

const PORT = 9010
const app = express()

app.use(express.json())
app.use(morgan(':method :url :status :res[content-length] - :response-time ms'));


app.post('/scrape', async(req, res) => {
    try{
        const {url} = req.body;

    if(!url){
        return req.status(403).json({
            success: "false",
            message: "URL is not found!"
        })
    }

    const html_content = await scrapeHtml(url)

    // const response  = await axios.post("http://37.27.81.8:5001/scrape", {
    const response  = await axios.post("http://127.0.0.1:5001/scrape", {
        url
    })

    if(response){
        return res.status(200).json({
            success: "true",
            message: "HTML content fetched successfully!",
            data: html_content
        })
    } else {
        return res.status(400).json({
            success: "false",
            message: "Something went wrong"
        })
    }

    } catch(error){
        console.log(error)
        return res.status(500).json({
            success: "false",
            message: "Internal Server Error!"
        })
    }
})


app.get('/', (req, res) => {
    res.send("The scrape engine is running 🚀 ........")
})

app.listen(PORT, () => {
    console.log(`Scraping Engine Started at ${PORT} 🚀..........`)
})

// This is function is used to read json data
function readJson(){
    try {
        const data = fs.readFileSync('./links.json', 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Error reading JSON file:', error);
        return null;
    }
}

// This is function is used to srape HTML content 
async function scrapeHtml(url){
    const browser = await puppeteer.launch({
        headless: false,
        args: [
            '--disable-gpu',
            '--disable-dev-shm-usage'
        ],
        defaultViewport: null
    });

    console.log("Browser Launched!")

    const page = await browser.newPage();
    
    await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36');

    console.log(`${url} this product data scraping started ...................`)

    await page.goto(url, {
        waitUntil: 'networkidle2',
        timeout: 0
    });

    await page.waitForSelector('body');

    const html = await page.evaluate(() => document.documentElement.outerHTML);

    const fs = require('fs');
    fs.writeFileSync('../py_scraper/output.html', html);

    console.log("HTML saved successfully.");

    await browser.close();

    return html;
}
