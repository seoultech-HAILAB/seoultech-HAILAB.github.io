/* The self-disclosing (SD) chatbot from our CHI EA 2025 study, replayed.
 *
 * The study's SD condition ran on a fixed conversation protocol: a numbered
 * script of what the bot discloses about itself and, after each disclosure, the
 * matching SISCO-AS list it asks the user about. That script is reproduced here
 * verbatim - the disclosures were never generated, they were authored, and a
 * model paraphrasing them would be a different study. What the model supplied
 * was the thread between them, and it does that here too: the acknowledgements
 * are live, through a Cloudflare Worker that holds the API key. The site is
 * static, so the key can never be in this file. If the Worker is unreachable the
 * conversation falls back to canned acknowledgements and still completes.
 *
 * The point of the condition is the ordering: the bot goes first every time. It
 * says it cannot sleep before it asks about sleep. The comparison condition
 * (NSD) asked the same questions with the disclosures removed, and that single
 * difference is what moved the outcomes. Only SD is rebuilt here; running the
 * control on a visitor would demonstrate nothing to them.
 *
 * The closing screen is the study's second half. A separate evaluator pass
 * scored the transcript against the SISCO-AS items; this reads back which of
 * those items the visitor's own words touched, so the assessment is visible as
 * something assembled from the conversation rather than asked as a form.
 */

const SCRIPT = [
  { from: 'bot', text: 'Hello! What is your name? 😊' },
  { from: 'bot', text: 'Nice to meet you! How was your day?', waitsFor: 'name' },
  { from: 'bot', text: 'Thanks for telling me. Actually, I came here today because I have something on my mind. If it’s okay with you, could you listen?' },
  {
    from: 'bot',
    disclosure: true,
    text: 'Despite my consistent efforts to study and memorize content, I often find it difficult to retain information, which leads to unsatisfactory grades. This ongoing challenge makes me feel frustrated and unmotivated. I’ve tried using flashcards, dedicating significant time to it, and I still ended up with average scores. It’s disheartening. Do you have any advice on how I can handle this better?',
  },
  { from: 'bot', text: 'Thank you, that genuinely helps. 🙏' },
  {
    from: 'bot',
    text: 'I’ve been feeling too stressed out lately, so I looked into it, and apparently these are the eight main causes of academic stress. I think I’ve been particularly stressed about the academic workload. What about you?',
    list: ['Intense competition', 'Assignment overload', 'Relationship with the professor', 'Evaluation', 'Academic workload', 'Course difficulty', 'Burden of class participation', 'Limited time'],
    group: 'causes',
  },
  { from: 'bot', follow: true },
  {
    from: 'bot',
    disclosure: true,
    text: 'As exam dates approach, I have more and more difficulty falling asleep and staying asleep. The lack of rest makes the stress worse, and I go into the exam already tired.',
  },
  {
    from: 'bot',
    text: 'Like the insomnia I’m dealing with, these are the symptoms that show up in the body. Have you ever had any of them? I’m curious whether it’s just me.',
    list: ['Sleep disorders', 'Chronic fatigue', 'Headaches or migraines', 'Digestive problems', 'Nail-biting', 'Drowsiness'],
    group: 'symptoms',
  },
  { from: 'bot', follow: true },
  {
    from: 'bot',
    disclosure: true,
    text: 'I often feel overwhelmed and powerless about my studies. It turns into a kind of belief that however much I put in, it will not come out the way I want.',
  },
  {
    from: 'bot',
    text: 'There are psychological changes too, much like what I’m going through. Have you noticed any of these?',
    list: ['Restlessness', 'Feelings of depression', 'Anxiety, distress, or desperation', 'Concentration problems', 'Increased aggression'],
    group: 'symptoms',
  },
  { from: 'bot', follow: true },
  {
    from: 'bot',
    disclosure: true,
    text: 'When the pressure is high I pull away from people and want to be on my own. Everything outside feels louder than usual, and it seems easier to just focus on studying.',
  },
  {
    from: 'bot',
    text: 'There are behavioural changes as well, much like wanting to be alone. Have you experienced any of these? I worry it might be only me.',
    list: ['Tendency to argue', 'Isolation from others', 'Lack of motivation', 'Increased or decreased food intake'],
    group: 'symptoms',
  },
  { from: 'bot', follow: true },
  {
    from: 'bot',
    disclosure: true,
    text: 'What helps me is talking it through with close friends. Saying it out loud and hearing that someone else has been there makes me feel less alone in it.',
  },
  {
    from: 'bot',
    text: 'Just as the causes and symptoms are known, there are known ways of coping. Do you have your own among these? If you share them in detail I think it would help me too.',
    list: ['Assertive skills', 'Developing a plan and executing tasks', 'Self-praise', 'Religious beliefs', 'Seeking information about the situation', 'Venting emotions and confiding in others'],
    group: 'coping',
  },
  { from: 'bot', follow: true },
  { from: 'bot', text: 'Thank you for sharing your stories! 💛' },
  { from: 'bot', text: 'Thanks to you, I was able to share my concerns and feel a bit lighter. Have a great day and see you again!', ends: true },
];

const ENDPOINT = 'https://hai-sd-chat.rubying1318.workers.dev';
// Worker source is tools/sd-chat.worker.js. After editing it:
// npx wrangler deploy -c wrangler-sd.toml

/* Used when the endpoint is unreachable, rate-limited, or slow. The conversation
   has to reach its end either way - a demo that stops halfway because a network
   call failed teaches the visitor nothing about the study. */
const ACKS = [
  'That makes sense to me. Could you tell me a bit more about it?',
  'I hear you. What does that look like on a normal week?',
  'Thank you for saying that. Is there more to it?',
  'That sounds heavy. How long has it been like that?',
];

/* The SISCO-AS items the evaluator scored, with the words a transcript actually
   uses for them. Deliberately shallow: this stands in for the scoring pass, and
   overstating what a keyword match can see would misrepresent the study. */
const ITEMS = {
  causes: {
    'Intense competition': ['compet', 'compare', 'rank', 'peer'],
    'Assignment overload': ['assignment', 'homework', 'deadline', 'too much work', 'project'],
    'Relationship with the professor': ['professor', 'advisor', 'supervisor', 'teacher'],
    'Evaluation': ['exam', 'grade', 'test', 'assessment', 'score', 'mark'],
    'Academic workload': ['workload', 'overwhelm', 'too much', 'busy', 'load'],
    'Course difficulty': ['difficult', 'hard', 'complex', 'understand', 'confusing'],
    'Burden of class participation': ['present', 'speak', 'participat', 'discussion', 'in front of'],
    'Limited time': ['time', 'late', 'rush', 'hours', 'schedule'],
  },
  symptoms: {
    'Sleep disorders': ['sleep', 'insomnia', 'awake', 'bed', 'night'],
    'Chronic fatigue': ['tired', 'fatigue', 'exhaust', 'drained', 'worn'],
    'Headaches or migraines': ['headache', 'migraine', 'head hurt'],
    'Digestive problems': ['stomach', 'nausea', 'digest', 'appetite', 'gut'],
    'Nail-biting': ['nail', 'bite', 'bitten'],
    'Drowsiness': ['drowsy', 'sleepy', 'doze', 'nap'],
    'Restlessness': ['restless', 'worry', 'worried', 'on edge', 'tense'],
    'Feelings of depression': ['depress', 'sad', 'hopeless', 'down', 'empty'],
    'Anxiety, distress, or desperation': ['anxious', 'anxiety', 'panic', 'desperate', 'nervous', 'scared'],
    'Concentration problems': ['concentrat', 'focus', 'distract', 'attention'],
    'Increased aggression': ['angry', 'anger', 'irritat', 'snap', 'aggress'],
    'Tendency to argue': ['argue', 'argument', 'fight', 'conflict'],
    'Isolation from others': ['alone', 'isolat', 'withdraw', 'avoid people', 'lonely'],
    'Lack of motivation': ['motivat', 'give up', 'pointless', 'care anymore', 'burn'],
    'Increased or decreased food intake': ['eat', 'food', 'meal', 'skip', 'snack'],
  },
  coping: {
    'Assertive skills': ['face it', 'confront', 'deal with', 'tackle', 'address'],
    'Developing a plan and executing tasks': ['plan', 'schedule', 'list', 'organis', 'organiz', 'priorit'],
    'Self-praise': ['reward', 'proud', 'praise', 'credit'],
    'Religious beliefs': ['pray', 'church', 'faith', 'religio', 'meditat', 'temple'],
    'Seeking information about the situation': ['look it up', 'research', 'read about', 'search', 'find out'],
    'Venting emotions and confiding in others': ['friend', 'talk', 'vent', 'family', 'tell someone', 'share'],
  },
};

const log = document.querySelector('[data-sd-log]');
const form = document.querySelector('[data-sd-form]');
const input = document.querySelector('[data-sd-input]');
const report = document.querySelector('[data-sd-report]');
const restart = document.querySelector('[data-sd-restart]');
if (log && form && input) {
  let step = 0;
  let awaiting = false;
  let followsLeft = 0;
  let ackIndex = 0;
  const said = [];
  const history = [];

  const bubble = (from, text, extra) => {
    const row = document.createElement('div');
    row.className = `sd-row sd-${from}`;
    const body = document.createElement('div');
    body.className = 'sd-bubble';
    if (extra && extra.disclosure) body.classList.add('is-disclosure');
    body.textContent = text;
    if (extra && extra.list) {
      const ul = document.createElement('ul');
      ul.className = 'sd-list';
      extra.list.forEach((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.appendChild(li);
      });
      body.appendChild(ul);
    }
    row.appendChild(body);
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
    return row;
  };

  const typing = () => {
    const row = document.createElement('div');
    row.className = 'sd-row sd-bot';
    row.innerHTML = '<div class="sd-bubble sd-typing"><span></span><span></span><span></span></div>';
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
    return row;
  };

  /* One live turn: the scripted disclosures are sent as the assistant's own
     history so the model answers in character and in context, rather than being
     asked to invent a persona each time. */
  const acknowledge = async () => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
    try {
      const response = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history.slice(-12) }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(String(response.status));
      const data = await response.json();
      const text = (data.reply || '').trim();
      if (!text) throw new Error('empty');
      history.push({ role: 'assistant', content: text });
      return text;
    } catch {
      const text = ACKS[ackIndex++ % ACKS.length];
      history.push({ role: 'assistant', content: text });
      return text;
    } finally {
      clearTimeout(timer);
    }
  };

  const finish = () => {
    form.hidden = true;
    const transcript = said.join(' ').toLowerCase();
    const found = {};
    let total = 0;
    Object.entries(ITEMS).forEach(([group, items]) => {
      found[group] = Object.entries(items)
        .filter(([, words]) => words.some((word) => transcript.includes(word)))
        .map(([label]) => label);
      total += found[group].length;
    });
    const section = (title, list) => `
      <div class="sd-report-group">
        <h3>${title}</h3>
        ${list.length ? `<ul>${list.map((item) => `<li>${item}</li>`).join('')}</ul>` : '<p class="sd-none">Nothing in what you wrote pointed here.</p>'}
      </div>`;
    report.innerHTML = `
      <p class="sd-report-lead">${total
        ? `The study ran a second pass over each transcript, scoring it against the SISCO Inventory of Academic Stress rather than asking anyone to fill the inventory in. Reading your side of this conversation the same way turns up <b>${total} item${total === 1 ? '' : 's'}</b>.`
        : 'The study ran a second pass over each transcript, scoring it against the SISCO Inventory of Academic Stress. Your side of this conversation was short enough that nothing scored — which is its own result, and the reason the SD condition mattered.'}</p>
      ${section('Causes', found.causes)}
      ${section('Symptoms', found.symptoms)}
      ${section('Coping strategies', found.coping)}
      <p class="sd-report-foot">Keyword matching stands in here for what a language model did in the study. The finding was not the scoring — it was that students talking to this version, the one that goes first, named their stressors more clearly and planned further ahead than students talking to a version that asked the same questions without disclosing anything.</p>`;
    report.hidden = false;
    if (restart) restart.hidden = false;
  };

  const advance = () => {
    if (step >= SCRIPT.length) return finish();
    const turn = SCRIPT[step];

    if (turn.follow) {
      if (followsLeft > 0) {
        followsLeft -= 1;
        awaiting = true;
        const ghost = typing();
        acknowledge()
          .then((text) => {
            ghost.remove();
            bubble('bot', text);
            awaiting = false;
          });
        return;
      }
      step += 1;
      return advance();
    }

    step += 1;
    awaiting = true;
    const ghost = typing();
    setTimeout(() => {
      ghost.remove();
      bubble('bot', turn.text, turn);
      history.push({ role: 'assistant', content: turn.text + (turn.list ? ' ' + turn.list.join(', ') : '') });
      if (turn.list) followsLeft = 2;
      if (turn.ends) {
        awaiting = false;
        return finish();
      }
      awaiting = false;
    }, turn.disclosure ? 1100 : 800);
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || awaiting) return;
    bubble('user', text);
    said.push(text);
    history.push({ role: 'user', content: text });
    input.value = '';
    advance();
  });

  if (restart) restart.addEventListener('click', () => window.location.reload());

  advance();
}
