const puppeteer = require('puppeteer');
const express = require('express')
const fs = require('fs');
const morgan = require('morgan')

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

    return res.status(200).json({
        success: "true",
        message: "HTML content fetched successfully!",
        data: html_content
    })
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

app.listen(9010, () => {
    console.log("Scraping Engine Started 🚀..........")
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
        executablePath: '/usr/bin/chromium-browser',
        headless: "new", 
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu',
            '--disable-dev-shm-usage'
        ]
    });

    console.log("Browser Launched!")

    const page = await browser.newPage();
    
    await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36');

    console.log(`${url} this product data scraping started ...................`)

    await page.goto(url, {
        waitUntil: 'networkidle2'
    });

    await page.waitForSelector('body');

    const html = await page.evaluate(() => document.documentElement.outerHTML);

    // const fs = require('fs');
    // fs.writeFileSync('output.html', html);

    console.log("HTML saved successfully.");

    await browser.close();

    return html;
}
