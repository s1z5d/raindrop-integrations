// https://github.com/dilame/instagram-private-api#examples
import { IgApiClient } from 'instagram-private-api';
import dotenv from 'dotenv';
import fetch from 'node-fetch';
import promisify from 'util';

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
  await ig.simulate.preLoginFlow();
  const loggedInUser = await ig.account.login(process.env.IG_USERNAME, process.env.IG_PASSWORD);
  // The same as preLoginFlow()
  // Optionally wrap it to process.nextTick so we dont need to wait ending of this bunch of requests
  process.nextTick(async () => await ig.simulate.postLoginFlow());
  // Create UserFeed instance to get loggedInUser's posts
  const savedFeed = ig.feed.saved(loggedInUser.pk);
  // let mySavedPostsFirstPage = await savedFeed.items()
  // savedFeed.items()
  let savedPosts = []
  savedFeed.items$.subscribe(
    posts => savedPosts.push(...posts),
    error => console.log(error),
    async () => {
      
      for (const sp of savedPosts) {
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
            excerpt: 'https://instagram.com/p/' + sp.code + '/'
          })
        });
        await new Promise(r => setTimeout(r, 1000));
      }
    }
  )
})();