/* analytics.js: a few named events sent to PostHog with a plain fetch. No PostHog script is loaded, so
   nothing records clicks, typing or the page, and no cookies are set. Callers pass only the event name and
   small labels such as the provider name; never pass a key, a question or an answer. Events from localhost are filtered out in PostHog as test traffic. */
const KEY = 'phc_BBU5JZBsZdND2yoNXRmULhqnxsko67WbgWl5nlN4eQK'; // Sunflower Studio project; public by design, filtered by app
const HOST = 'https://us.i.posthog.com';     // or https://eu.i.posthog.com for an EU project

// anonymous id for this browser tab only; it is never tied to a person
function anonId(){
  try{
    let id = sessionStorage.getItem('pots_anon_id');
    if(!id){ id = crypto.randomUUID(); sessionStorage.setItem('pots_anon_id', id); }
    return id;
  }catch{ return 'anon'; }
}

const APP = 'pots_findings';                 // on every event, per the project-prefix convention (prefix pots_)

export function track(event, props = {}){
  if(!KEY) return;
  try{
    fetch(`${HOST}/i/v0/e/`, { method:'POST', keepalive:true, headers:{'content-type':'application/json'},
      body: JSON.stringify({ api_key:KEY, event, distinct_id:anonId(),
        properties:{ ...props, app:APP, path:location.pathname, $process_person_profile:false, $geoip_disable:true } }) }).catch(()=>{});
  }catch{}
}

// Ask page: ask_provider_selected, ask_key_saved, ask_question_sent
export const trackAsk = (event, props) => track(`ask_${event}`, props);
