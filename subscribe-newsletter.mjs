import puppeteer from 'puppeteer-core';

const EMAIL = 'hanpaas.hermes@claw.163.com';

// Find Chrome executable
const CHROME_PATHS = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
];

async function findChrome() {
  const { accessSync, constants } = await import('fs');
  for (const p of CHROME_PATHS) {
    try { accessSync(p, constants.X_OK); return p; } catch {}
  }
  throw new Error('Chrome not found');
}

async function subscribe(url, name) {
  console.log(`\n=== ${name} ===`);
  console.log(`Opening ${url}...`);
  
  const browser = await puppeteer.launch({
    executablePath: await findChrome(),
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 20000 });
    
    // Try to find email input and submit button
    const inputs = await page.$$('input[type="email"], input[name="email"], input[placeholder*="email" i], input[placeholder*="Email" i], input[placeholder*="邮箱" i]');
    
    if (inputs.length === 0) {
      // Try broader search
      const allInputs = await page.$$('input');
      console.log(`  Found ${allInputs.length} input fields`);
      
      let emailFound = false;
      for (const input of allInputs) {
        const type = await input.evaluate(el => el.type);
        const placeholder = (await input.evaluate(el => el.placeholder || '')).toLowerCase();
        const name = (await input.evaluate(el => el.name || '')).toLowerCase();
        const id = (await input.evaluate(el => el.id || '')).toLowerCase();
        const className = (await input.evaluate(el => el.className || '')).toLowerCase();
        
        if (type === 'email' || placeholder.includes('email') || name === 'email' || id.includes('email') || className.includes('email')) {
          await input.type(EMAIL, { delay: 50 });
          emailFound = true;
          console.log(`  ✅ Filled email into: type=${type}, placeholder="${placeholder}", name="${name}"`);
          
          // Try to find a submit button
          const submitBtn = await page.$('button[type="submit"], button:has-text("Subscribe"), button:has-text("submit"), button:has-text("Sign Up"), button:has-text("Get"), a:has-text("Subscribe"), input[type="submit"]');
          if (submitBtn) {
            await submitBtn.click();
            console.log('  ✅ Clicked submit button');
          } else {
            // Try pressing Enter
            await input.press('Enter');
            console.log('  ✅ Pressed Enter');
          }
          break;
        }
      }
      
      if (!emailFound) {
        // Save screenshot for debugging
        await page.screenshot({ path: `/tmp/${name.replace(/[^a-z0-9]/gi, '_')}.png` });
        console.log(`  ❌ No email input found. Screenshot saved.`);
        
        // Print page text for debugging
        const text = await page.evaluate(() => document.body.innerText.substring(0, 2000));
        console.log(`  Page text snippet: ${text.substring(0, 500)}`);
      }
    } else {
      const input = inputs[0];
      await input.type(EMAIL, { delay: 50 });
      console.log('  ✅ Filled email input');
      
      const submitBtn = await page.$('button[type="submit"], button:has-text("Subscribe"), button:has-text("submit"), input[type="submit"]');
      if (submitBtn) {
        await submitBtn.click();
        console.log('  ✅ Clicked submit button');
      } else {
        await input.press('Enter');
        console.log('  ✅ Pressed Enter');
      }
    }
    
    await new Promise(r => setTimeout(r, 2000));
    
    // Check for success message or error
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 1000));
    console.log(`  Response: ${bodyText.substring(0, 300)}`);
    
  } catch (err) {
    console.log(`  ❌ Error: ${err.message}`);
    try {
      await page.screenshot({ path: `/tmp/${name.replace(/[^a-z0-9]/gi, '_')}.png` });
      console.log(`  Screenshot saved for debugging`);
    } catch {}
  }
  
  await browser.close();
}

const newsletters = [
  { url: 'https://www.therundown.ai', name: 'The Rundown AI' },
  { url: 'https://tldr.tech', name: 'TLDR AI' },
  { url: 'https://www.theneurondaily.com', name: 'The Neuron' },
  { url: 'https://bensbites.com', name: "Ben's Bites" },
  { url: 'https://www.latent.space', name: 'Latent Space' },
  { url: 'https://smol.ai/news', name: 'Smol AI News' },
  { url: 'https://www.interconnects.ai', name: 'Interconnects' },
  { url: 'https://www.oneusefulthing.org', name: 'One Useful Thing' },
  { url: 'https://aibreakfast.beehiiv.com', name: 'AI Breakfast' },
  { url: 'https://every.to', name: 'Every' },
];

const target = newsletters.find(n => n.url === process.argv[2] || n.name === process.argv[2]);
if (target) {
  await subscribe(target.url, target.name);
} else {
  console.log('Usage: node subscribe-newsletter.mjs <url or name>');
  console.log('Available:');
  newsletters.forEach(n => console.log(`  ${n.name}: ${n.url}`));
}
