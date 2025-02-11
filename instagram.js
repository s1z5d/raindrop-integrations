// https://github.com/dilame/instagram-private-api#examples
// Use Node 14 -- higher version kill unhandled promise errors, an instance of which is thrown at some point by the API library(?)
import { IgApiClient } from 'instagram-private-api';
import dotenv from 'dotenv';
import fetch from 'node-fetch';
import fs from 'fs/promises';
import { generateToken } from 'node-2fa';

dotenv.config()
const ig = new IgApiClient();
// You must generate device id's before login.
// Id's generated based on seed
// So if you pass the same value as first argument - the same id's are generated every time
ig.state.generateDevice(process.env.IG_USERNAME);
// Optionally you can setup proxy url
ig.state.proxyUrl = process.env.IG_PROXY;
(async () => {
  // Execute all requests prior to authorization in the real Android application
  // Not required but recommended
  try {
    await ig.simulate.preLoginFlow();
  } catch (err) {
    console.log(err);
  }
  let loggedInUser;
  try {
    loggedInUser = await ig.account.login(process.env.IG_USERNAME, process.env.IG_PASSWORD);
  } catch (err) {
    const username = err.response.body.two_factor_info.username;
    const twoFactorIdentifier = err.response.body.two_factor_info.two_factor_identifier;
    loggedInUser = await ig.account.twoFactorLogin({
      username,
      verificationCode: generateToken(process.env.IG_2FA).token,
      twoFactorIdentifier,
      verificationMethod: '0',
      trustThisDevice: '1',
    });
  }
  // The same as preLoginFlow()
  // Optionally wrap it to process.nextTick so we dont need to wait ending of this bunch of requests
  process.nextTick(async () => await ig.simulate.postLoginFlow());
  // Create UserFeed instance to get loggedInUser's posts
  const savedFeed = ig.feed.saved(loggedInUser.pk);
  // Read existing saved links
  let alreadySavedPosts = '';
  try {
    alreadySavedPosts = await fs.readFile('instagram.txt');
  } catch {
    await fs.writeFile('instagram.txt', '');
  }
  let savedPosts = [];
  let found = false;
  while (!found) {
    const posts = await savedFeed.items();
    for (const p of posts) {
      if (alreadySavedPosts.includes(p.code)) {
        found = true;
        break;
      } else {
        savedPosts.push(p);
      }
    }
  }
  const newPosts = savedPosts.filter(sp => !alreadySavedPosts.includes(sp.code));
  console.log(`Saving ${newPosts.length} Instagram post(s)...`);
  let i = 1;
  for (const sp of newPosts) {
    const res = await fetch('https://api.raindrop.io/rest/v1/raindrop', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + process.env.RAINDROP_TOKEN,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        link: 'https://instagram.com/p/' + sp.code + '/',
        tags: ['instagram'],
        title: sp.user.full_name + ' on Instagram',
        excerpt: 'https://instagram.com/p/' + sp.code + '/\n\n' + (sp.caption ? sp.caption.text : '')
      })
    });

    console.log(`Saved ${i} out of ${newPosts.length} posts (${sp.code}).`);
    i++;

    await fs.appendFile('instagram.txt', sp.code + '\n')
    
    await new Promise(r => setTimeout(r, 1000));
  }
})();