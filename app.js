const APP_VERSION = 1;
const STORAGE_KEY = "iotQuizProgressV1";
const CONSENT_COOKIE = "iotQuizConsent";
const MANIFEST_URL = "./questions_json/manifest.json";
const U1_CHAPTER_CATALOG_URL = "./questions_json/u1-chapters.json";

const app = document.querySelector("#app");
const resetButton = document.querySelector("#reset-progress-btn");
const cookieDialog = document.querySelector("#cookie-dialog");
const cookieAcceptButton = document.querySelector("#cookie-accept-btn");

let manifest = [];
let currentQuiz = null;
let u1ChapterCatalog = null;

const questionFileCache = new Map();
/* -------------------------------------------------------
 * Cookie 與 localStorage
 * ----------------------------------------------------- */

function setCookie(name, value, days = 365) {
  const maxAge = days * 24 * 60 * 60;

  document.cookie =
    `${encodeURIComponent(name)}=${encodeURIComponent(value)}; ` +
    `max-age=${maxAge}; path=/; SameSite=Lax; Secure`;
}

function getCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`;

  return (
    document.cookie
      .split(";")
      .map((item) => item.trim())
      .find((item) => item.startsWith(prefix))
      ?.slice(prefix.length) ?? null
  );
}

function showConsentIfNeeded() {
  if (!cookieDialog) {
    return;
  }

  if (!getCookie(CONSENT_COOKIE)) {
    cookieDialog.showModal();
  }
}

if (cookieAcceptButton) {
  cookieAcceptButton.addEventListener("click", () => {
    setCookie(CONSENT_COOKIE, "accepted");
  });
}

function defaultProgress() {
  return {
    version: APP_VERSION,
    questions: {},
    practiceDates: {},
  };
}

function loadProgress() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return defaultProgress();
    }

    const value = JSON.parse(raw);

    if (
      !value ||
      value.version !== APP_VERSION ||
      typeof value.questions !== "object"
    ) {
      return defaultProgress();
    }

    // 相容舊版本紀錄
    if (!value.practiceDates || typeof value.practiceDates !== "object") {
      value.practiceDates = {};
    }

    for (const item of Object.values(value.questions)) {
      if (typeof item.everCorrect !== "boolean") {
        item.everCorrect = item.lastCorrect === true;
      }

      if (typeof item.correctCount !== "number") {
        item.correctCount = item.lastCorrect === true ? 1 : 0;
      }
    }

    return value;
  } catch (error) {
    console.warn("讀取本機作答紀錄失敗：", error);
    return defaultProgress();
  }
}
function saveProgress(progress) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch (error) {
    console.error("儲存本機作答紀錄失敗：", error);
    alert("無法儲存作答紀錄，可能是瀏覽器禁止本機儲存或空間不足。");
  }
}

function questionKey(sourceFile, questionId) {
  return `${sourceFile}::${questionId}`;
}

function updateProgress(sourceFile, question, isCorrect) {
  const progress = loadProgress();
  const key = questionKey(sourceFile, question.id);

  const previous = progress.questions[key] ?? {
    attempted: false,
    attempts: 0,
    correctCount: 0,
    wrongCount: 0,
    everCorrect: false,
    lastCorrect: null,
  };

  previous.attempted = true;
  previous.attempts += 1;
  previous.lastCorrect = isCorrect;
  previous.lastAnsweredAt = new Date().toISOString();

  if (isCorrect) {
    previous.correctCount += 1;
    previous.everCorrect = true;
  } else {
    previous.wrongCount += 1;
  }

  progress.questions[key] = previous;
  saveProgress(progress);
}

function removeWrongRecord(sourceFile, questionId) {
  const progress = loadProgress();
  const key = questionKey(sourceFile, questionId);
  const item = progress.questions[key];

  if (!item) {
    return;
  }

  item.wrongCount = 0;
  progress.questions[key] = item;

  saveProgress(progress);
}

/* -------------------------------------------------------
 * 共用工具
 * ----------------------------------------------------- */

function shuffle(items) {
  const result = [...items];

  for (let i = result.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }

  return result;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function fetchJson(url) {
  const response = await fetch(url, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`讀取失敗：${url}，HTTP ${response.status}`);
  }

  return response.json();
}

async function loadManifest() {
  const data = await fetchJson(MANIFEST_URL);

  if (!Array.isArray(data.files)) {
    throw new Error("manifest.json 格式錯誤：缺少 files 陣列");
  }

  manifest = data.files;
}

async function loadU1ChapterCatalog() {
  if (u1ChapterCatalog) {
    return u1ChapterCatalog;
  }

  const data = await fetchJson(U1_CHAPTER_CATALOG_URL);

  if (data.subject !== "U1" || !Array.isArray(data.chapters)) {
    throw new Error("U1 章節目錄格式錯誤");
  }

  u1ChapterCatalog = data;
  return data;
}

function parseFileInfo(file) {
  const match = file.match(/^(\d{3})-(1|2)-(U1|U2)\.json$/i);

  if (!match) {
    return null;
  }

  return {
    file,
    year: Number(match[1]),
    session: Number(match[2]),
    subject: match[3].toUpperCase(),
  };
}

function availableFiles(subject = null) {
  return manifest
    .map(parseFileInfo)
    .filter(Boolean)
    .filter((item) => !subject || item.subject === subject)
    .sort(
      (a, b) =>
        a.year - b.year ||
        a.session - b.session ||
        a.subject.localeCompare(b.subject),
    );
}

function progressStats() {
  const values = Object.values(loadProgress().questions);

  return {
    attempted: values.filter((value) => value.attempted).length,
    wrong: values.filter((value) => value.wrongCount > 0).length,
    totalAttempts: values.reduce(
      (sum, value) => sum + (value.attempts || 0),
      0,
    ),
  };
}

/* -------------------------------------------------------
 * 首頁
 * ----------------------------------------------------- */

async function renderHome() {
  app.innerHTML = `
    <section class="panel">
      <p>正在整理題庫進度……</p>
    </section>
  `;

  try {
    // 必須先取得 U1、U2 的題庫與學習統計
    const [u1, u2] = await Promise.all([
      calculateSubjectStats("U1"),
      calculateSubjectStats("U2"),
    ]);

    const progress = loadProgress();
    const allProgressItems = Object.values(progress.questions);

    const totalAttempts = allProgressItems.reduce(
      (sum, item) => sum + (item.attempts ?? 0),
      0,
    );

    const wrongCount = allProgressItems.filter(
      (item) => (item.wrongCount ?? 0) > 0,
    ).length;

    app.innerHTML = `
      <section class="panel">

        <!-- 選擇練習模式移到最上方 -->
        <section class="dashboard-section dashboard-section-first">
          <h2>選擇練習模式</h2>

          <div class="grid">
            <article class="card mode-card">
              <h3>IPAS 歷屆年度測驗</h3>

              <p>
                選擇物聯網應用工程師 U1 或 U2 科目，再指定年度與場次，
                練習 IPAS 題庫中的歷屆試題。
              </p>

              <button class="primary" data-mode="year">
                開始設定
              </button>
            </article>

            <article class="card mode-card">
              <h3>AIOT 隨機題庫測驗</h3>

              <p>
                從物聯網應用工程師題庫優先抽選未做過的題目，
                不足時再由已做題補足最多 50 題。
              </p>

              <button class="primary" data-mode="random">
                開始設定
              </button>
            </article>

            <article class="card mode-card chapter-mode-card">
              <span class="badge">僅 U1</span>
              <h3>U1 依章節刷題</h3>

              <p>
                依「AIoT 基礎概論」學習指引的九個單元選題，
                集中練習同一知識主題，不會混入 U2 題目。
              </p>

              <button class="primary" data-mode="chapter">
                選擇章節
              </button>
            </article>

            <article class="card mode-card">
              <h3>物聯網錯題複習</h3>

              <p>
                從目前瀏覽器的 IPAS 題庫錯題紀錄中，
                隨機抽選最多 20 題進行複習。
              </p>

              <button class="primary" data-mode="wrong">
                開始設定
              </button>
            </article>
          </div>
        </section>

        <!-- 學習進度 -->
        <section class="dashboard-section">
          <h2>學習進度</h2>

          <div class="stats">
            <div class="stat">
              <strong>${u1.attempted + u2.attempted}</strong>
              <span>曾經做過</span>
            </div>

            <div class="stat">
              <strong>${wrongCount}</strong>
              <span>目前錯題</span>
            </div>

            <div class="stat">
              <strong>${totalAttempts}</strong>
              <span>累積作答次數</span>
            </div>
          </div>
        </section>

        <!-- 題庫完成度 -->
        <section class="dashboard-section">
          <h2>題庫完成度</h2>

          <div class="subject-progress-grid">
            ${renderSubjectProgressCard(
              "物聯網基礎架構概論（U1）",
              u1,
              "completion",
            )}

            ${renderSubjectProgressCard(
              "物聯網系統與應用（U2）",
              u2,
              "completion",
            )}
          </div>
        </section>

        <!-- 答對覆蓋率 -->
        <section class="dashboard-section">
          <h2>答對題目覆蓋率</h2>

          <div class="subject-progress-grid">
            ${renderSubjectProgressCard(
              "物聯網基礎架構概論（U1）",
              u1,
              "correct",
            )}

            ${renderSubjectProgressCard(
              "物聯網系統與應用（U2）",
              u2,
              "correct",
            )}
          </div>
        </section>

        <!-- 每日簽到 -->
        ${renderPracticeCalendar()}

      </section>
    `;

    // 重新綁定三個模式按鈕
    app.querySelectorAll("[data-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        renderModeSetup(button.dataset.mode);
      });
    });
  } catch (error) {
    console.error("首頁載入失敗：", error);

    app.innerHTML = `
      <section class="panel">
        <h2 class="error">無法計算學習進度</h2>

        <p>${escapeHtml(error.message)}</p>

        <div class="actions">
          <button class="secondary" id="reload-home">
            重新載入
          </button>
        </div>
      </section>
    `;

    app
      .querySelector("#reload-home")
      .addEventListener("click", renderHome);
  }
}

function renderSubjectProgressCard(title, stats, mode) {
  const isCompletion = mode === "completion";

  const rate = isCompletion
    ? stats.completionRate
    : stats.correctCoverageRate;

  const numerator = isCompletion
    ? stats.attempted
    : stats.everCorrect;

  const label = isCompletion
    ? "完成度"
    : "答對覆蓋率";

  return `
    <article class="card subject-progress-card">
      <div>
        <h3>${escapeHtml(title)}</h3>

        <p>
          ${label}：
          <strong>${rate}%</strong>
          (${numerator}/${stats.total})
        </p>

        ${
          !isCompletion
            ? `
              <p class="note">
                已作答正確率：
                ${stats.attemptedAccuracy}%
                (${stats.everCorrect}/${stats.attempted})
              </p>
            `
            : ""
        }
      </div>

      ${progressPie(rate, `${rate}%`)}
    </article>
  `;
}

function subjectSelectHtml() {
  return `
    <div class="field">
      <label for="subject">科目</label>

      <select id="subject">
        <option value="U1">
          物聯網基礎架構概論（U1）
        </option>

        <option value="U2">
          物聯網系統與應用（U2）
        </option>
      </select>
    </div>
  `;
}

function renderModeSetup(mode) {
  if (mode === "year") {
    renderYearSetup();
    return;
  }

  if (mode === "random") {
    renderRandomSetup();
    return;
  }

  if (mode === "wrong") {
    renderWrongSetup();
    return;
  }

  if (mode === "chapter") {
    renderChapterSetup();
  }
}

/* -------------------------------------------------------
 * 年度測驗設定
 * ----------------------------------------------------- */

function renderYearSetup() {
  app.innerHTML = `
    <section class="panel">
      <h2>IPAS 歷屆年度測驗設定</h2>

      ${subjectSelectHtml()}

      <div class="field">
        <label for="exam-file">年度與場次</label>
        <select id="exam-file"></select>
      </div>

      <div class="field">
        <label for="year-question-count">本次題數</label>
        <select id="year-question-count">
          <option value="5">5 題</option>
          <option value="10">10 題</option>
          <option value="20">20 題</option>
          <option value="50" selected>50 題（完整試題）</option>
        </select>
      </div>

      <p class="note">
        系統會從所選年度隨機抽取指定題數，題目與選項順序都會重新打亂。
      </p>

      <div class="actions spread">
        <button class="secondary" id="back">
          返回
        </button>

        <button class="primary" id="start">
          開始測驗
        </button>
      </div>
    </section>
  `;

  const subjectSelect = app.querySelector("#subject");
  const fileSelect = app.querySelector("#exam-file");
  const questionCountSelect = app.querySelector("#year-question-count");
  const startButton = app.querySelector("#start");

  function refreshFiles() {
    const files = availableFiles(subjectSelect.value);

    if (!files.length) {
      fileSelect.innerHTML = `
        <option value="">
          尚無題庫
        </option>
      `;

      startButton.disabled = true;
      return;
    }

    fileSelect.innerHTML = files
      .map(
        (item) => `
          <option value="${escapeHtml(item.file)}">
            ${item.year}-${item.session}
          </option>
        `,
      )
      .join("");

    startButton.disabled = false;
  }

  subjectSelect.addEventListener("change", refreshFiles);
  refreshFiles();

  app.querySelector("#back").addEventListener("click", renderHome);

  startButton.addEventListener("click", async () => {
    if (!fileSelect.value) {
      return;
    }

    await startYearQuiz(
      fileSelect.value,
      Number(questionCountSelect.value),
    );
  });
}

/* -------------------------------------------------------
 * 隨機測驗設定
 * ----------------------------------------------------- */

function renderRandomSetup() {
  app.innerHTML = `
    <section class="panel">
      <h2>AIOT 隨機題庫測驗設定</h2>

      ${subjectSelectHtml()}

      <div class="field">
        <label for="random-question-count">本次題數</label>
        <select id="random-question-count">
          <option value="5">5 題</option>
          <option value="10">10 題</option>
          <option value="20">20 題</option>
          <option value="50" selected>50 題</option>
        </select>
      </div>

      <p class="note">
        系統會從該科目所有題庫中合併後，
        優先隨機抽選未做過的題目，不足時再由已做題補足。
      </p>

      <div class="actions spread">
        <button class="secondary" id="back">
          返回
        </button>

        <button class="primary" id="start">
          開始測驗
        </button>
      </div>
    </section>
  `;

  app.querySelector("#back").addEventListener("click", renderHome);

  app.querySelector("#start").addEventListener("click", async () => {
    const subject = app.querySelector("#subject").value;
    const requestedCount = Number(
      app.querySelector("#random-question-count").value,
    );
    await startRandomQuiz(subject, requestedCount);
  });
}

/* -------------------------------------------------------
 * U1 章節刷題設定
 * ----------------------------------------------------- */

async function renderChapterSetup() {
  app.innerHTML = `
    <section class="panel">
      <p>正在載入 U1 章節目錄……</p>
    </section>
  `;

  try {
    const catalog = await loadU1ChapterCatalog();
    const availableChapters = catalog.chapters.filter(
      (chapter) => chapter.questionCount > 0,
    );

    app.innerHTML = `
      <section class="panel">
        <div class="quiz-head">
          <div>
            <span class="badge">U1 專屬</span>
            <h2>依學習指引章節刷題</h2>
          </div>
        </div>

        <p class="note">
          分類依據：AIoT 應用工程師（初級）學習指引－科目 1。
          本模式只讀取檔名為 <code>*-U1.json</code> 的題庫。
        </p>

        <div class="field">
          <label for="chapter">章節</label>
          <select id="chapter">
            ${availableChapters
              .map(
                (chapter) => `
                  <option value="${escapeHtml(chapter.id)}">
                    ${escapeHtml(chapter.id)} ${escapeHtml(chapter.name)}（${chapter.questionCount} 題）
                  </option>
                `,
              )
              .join("")}
          </select>
        </div>

        <div id="chapter-description" class="chapter-description"></div>

        <div class="field">
          <label for="question-count">本次題數</label>
          <select id="question-count">
            <option value="10">10 題</option>
            <option value="20" selected>20 題</option>
            <option value="30">30 題</option>
            <option value="50">50 題</option>
          </select>
        </div>

        <p class="note">同一章節會優先抽選尚未做過的題目；不足時再由已做題補足。</p>

        <div class="actions spread">
          <button class="secondary" id="back">返回</button>
          <button class="primary" id="start">開始章節刷題</button>
        </div>
      </section>
    `;

    const chapterSelect = app.querySelector("#chapter");
    const description = app.querySelector("#chapter-description");

    function refreshDescription() {
      const chapter = availableChapters.find(
        (item) => item.id === chapterSelect.value,
      );

      description.innerHTML = chapter
        ? `<strong>${escapeHtml(chapter.name)}</strong><p>${escapeHtml(chapter.description)}</p>`
        : "";
    }

    chapterSelect.addEventListener("change", refreshDescription);
    refreshDescription();

    app.querySelector("#back").addEventListener("click", renderHome);
    app.querySelector("#start").addEventListener("click", async () => {
      const chapter = availableChapters.find(
        (item) => item.id === chapterSelect.value,
      );
      const count = Number(app.querySelector("#question-count").value);

      if (chapter) {
        await startChapterQuiz(chapter, count);
      }
    });
  } catch (error) {
    console.error(error);
    app.innerHTML = `
      <section class="panel">
        <h2 class="error">無法載入 U1 章節</h2>
        <p>${escapeHtml(error.message)}</p>
        <div class="actions"><button class="secondary" id="back">返回首頁</button></div>
      </section>
    `;
    app.querySelector("#back").addEventListener("click", renderHome);
  }
}

/* -------------------------------------------------------
 * 錯題測驗設定
 * ----------------------------------------------------- */

function renderWrongSetup() {
  const progress = loadProgress();

  const wrongKeys = Object.entries(progress.questions)
    .filter(([, value]) => value.wrongCount > 0)
    .map(([key]) => key);

  app.innerHTML = `
    <section class="panel">
      <h2>物聯網錯題複習測驗設定</h2>

      ${subjectSelectHtml()}

      <p>
        目前裝置共有
        <strong>${wrongKeys.length}</strong>
        題錯題紀錄。
      </p>

      <p class="note">
        每次最多抽選 20 題。
        完成後可勾選要從錯題庫移除的題目。
      </p>

      <div class="actions spread">
        <button class="secondary" id="back">
          返回
        </button>

        <button
          class="primary"
          id="start"
          ${wrongKeys.length ? "" : "disabled"}
        >
          開始測驗
        </button>
      </div>
    </section>
  `;

  app.querySelector("#back").addEventListener("click", renderHome);

  app.querySelector("#start").addEventListener("click", async () => {
    const subject = app.querySelector("#subject").value;
    await startWrongQuiz(subject);
  });
}

/* -------------------------------------------------------
 * 題庫讀取
 * ----------------------------------------------------- */

async function loadQuestionFile(file) {
  if (questionFileCache.has(file)) {
    return questionFileCache.get(file).map((question) => ({
      ...question,
      options: question.options.map((option) => ({ ...option })),
    }));
  }

  const url = `./questions_json/${encodeURIComponent(file)}`;
  const data = await fetchJson(url);

  if (!Array.isArray(data.questions)) {
    throw new Error(`${file} 缺少 questions 陣列`);
  }

  const questions = data.questions.map((question) => ({
    ...question,
    sourceFile: file,
    options: Array.isArray(question.options)
      ? question.options.map((option) => ({ ...option }))
      : [],
  }));

  questionFileCache.set(file, questions);

  return questions.map((question) => ({
    ...question,
    options: question.options.map((option) => ({ ...option })),
  }));
}

function prepareQuestions(questions) {
  return shuffle(questions).map((question) => ({
    ...question,
    options: shuffle(question.options),
    selectedOptionIds: [],
  }));
}

async function startYearQuiz(file, requestedCount = 50) {
  await withLoading(async () => {
    const questions = await loadQuestionFile(file);

    if (!questions.length) {
      throw new Error(`${file} 沒有題目`);
    }

    const targetCount = Math.min(requestedCount, questions.length);
    const selected = shuffle(questions).slice(0, targetCount);

    currentQuiz = {
      mode: "year",
      title: `${file.replace(".json", "")} 年度測驗（${targetCount} 題）`,
      questions: prepareQuestions(selected),
      currentIndex: 0,
    };

    renderQuestion();
  });
}

async function startRandomQuiz(subject, requestedCount = 50) {
  await withLoading(async () => {
    const files = availableFiles(subject);

    if (!files.length) {
      throw new Error(`找不到 ${subject} 題庫`);
    }

    const groups = await Promise.all(
      files.map((item) => loadQuestionFile(item.file)),
    );

    const pool = groups.flat();

    if (!pool.length) {
      throw new Error(`${subject} 題庫沒有題目`);
    }

    const progress = loadProgress();

    const unattempted = [];
    const attempted = [];

    for (const question of pool) {
      const key = questionKey(
        question.sourceFile,
        question.id,
      );

      const record = progress.questions[key];

      if (record?.attempted) {
        attempted.push(question);
      } else {
        unattempted.push(question);
      }
    }

    const targetCount = Math.min(requestedCount, pool.length);

    // 優先未做題目
    const selected = shuffle(unattempted).slice(0, targetCount);

    // 未做題目不足時，再由已做題補足
    if (selected.length < targetCount) {
      const remainingCount = targetCount - selected.length;

      selected.push(
        ...shuffle(attempted).slice(0, remainingCount),
      );
    }

    currentQuiz = {
      mode: "random",
      title: `${subject} 隨機測驗（${targetCount} 題）`,
      questions: prepareQuestions(selected),
      currentIndex: 0,
    };

    renderQuestion();
  });
}

async function startChapterQuiz(chapter, requestedCount) {
  await withLoading(async () => {
    // Deliberately hard-coded to U1: chapter metadata belongs to subject 1 only.
    const files = availableFiles("U1");
    const groups = await Promise.all(
      files.map((item) => loadQuestionFile(item.file)),
    );
    const pool = groups
      .flat()
      .filter((question) => question.chapterId === chapter.id);

    if (!pool.length) {
      throw new Error(`「${chapter.name}」目前沒有可用的 U1 題目`);
    }

    const progress = loadProgress();
    const unattempted = [];
    const attempted = [];

    for (const question of pool) {
      const key = questionKey(question.sourceFile, question.id);
      if (progress.questions[key]?.attempted) {
        attempted.push(question);
      } else {
        unattempted.push(question);
      }
    }

    const targetCount = Math.min(requestedCount, pool.length);
    const selected = shuffle(unattempted).slice(0, targetCount);

    if (selected.length < targetCount) {
      selected.push(
        ...shuffle(attempted).slice(0, targetCount - selected.length),
      );
    }

    currentQuiz = {
      mode: "chapter",
      subject: "U1",
      chapterId: chapter.id,
      chapterName: chapter.name,
      title: `U1 ${chapter.id} ${chapter.name}`,
      questions: prepareQuestions(selected),
      currentIndex: 0,
    };

    renderQuestion();
  });
}

async function startWrongQuiz(subject) {
  await withLoading(async () => {
    const progress = loadProgress();
    const files = availableFiles(subject);

    if (!files.length) {
      throw new Error(`找不到 ${subject} 題庫`);
    }

    const groups = await Promise.all(
      files.map((item) => loadQuestionFile(item.file)),
    );

    const pool = groups
      .flat()
      .filter((question) => {
        const key = questionKey(
          question.sourceFile,
          question.id,
        );

        const state = progress.questions[key];

        return state?.wrongCount > 0;
      });

    if (!pool.length) {
      throw new Error(`${subject} 目前沒有錯題紀錄`);
    }

    currentQuiz = {
      mode: "wrong",
      title: `${subject} 錯題測驗`,
      questions: prepareQuestions(
        shuffle(pool).slice(0, Math.min(20, pool.length)),
      ),
      currentIndex: 0,
    };

    renderQuestion();
  });
}

async function withLoading(task) {
  app.innerHTML = `
    <section class="panel">
      <p>題庫載入中……</p>
    </section>
  `;

  try {
    await task();
  } catch (error) {
    console.error(error);

    app.innerHTML = `
      <section class="panel">
        <h2 class="error">無法開始測驗</h2>

        <p>${escapeHtml(error.message)}</p>

        <div class="actions">
          <button class="secondary" id="back">
            返回首頁
          </button>
        </div>
      </section>
    `;

    app.querySelector("#back").addEventListener("click", renderHome);
  }
}

/* -------------------------------------------------------
 * 作答判斷
 * ----------------------------------------------------- */

function correctOptionIds(question) {
  return question.options
    .filter((option) => option.isCorrect)
    .map((option) => String(option.id));
}

function selectedIsCorrect(question) {
  const correct = [...correctOptionIds(question)].sort();
  const selected = [...question.selectedOptionIds]
    .map(String)
    .sort();

  return (
    correct.length === selected.length &&
    correct.every((id, index) => id === selected[index])
  );
}

/* -------------------------------------------------------
 * 題目畫面
 * ----------------------------------------------------- */

function renderQuestion() {
  const quiz = currentQuiz;
  const question = quiz.questions[quiz.currentIndex];
  const total = quiz.questions.length;
  const number = quiz.currentIndex + 1;

  const correctCount = correctOptionIds(question).length;
  const multiple = correctCount > 1;
  const inputType = multiple ? "checkbox" : "radio";

  app.innerHTML = `
    <section class="panel">
      <div class="quiz-head">
        <div>
          <strong>${escapeHtml(quiz.title)}</strong>
          <span class="badge">${number} / ${total}</span>
        </div>

        <button class="secondary" id="quit">
          結束測驗
        </button>
      </div>

      <div class="progress" aria-label="作答進度">
        <div style="width: ${(number / total) * 100}%"></div>
      </div>

      <h2 class="question-title">
        ${escapeHtml(question.question)}
      </h2>

      ${
        question.chapterId
          ? `<p class="chapter-label"><span class="badge">${escapeHtml(question.chapterId)}</span> ${escapeHtml(question.chapterName)}</p>`
          : ""
      }

      ${
        multiple
          ? `
            <p class="warning">
              本題有多個正確答案，請選出全部正確選項。
            </p>
          `
          : ""
      }

      <div class="option-list">
        ${question.options
          .map(
            (option, index) => `
              <label class="option">
                <input
                  type="${inputType}"
                  name="answer"
                  value="${escapeHtml(option.id)}"
                  ${
                    question.selectedOptionIds.includes(
                      String(option.id),
                    )
                      ? "checked"
                      : ""
                  }
                >

                <span>
                  <strong>
                    ${String.fromCharCode(65 + index)}.
                  </strong>

                  ${escapeHtml(option.text)}
                </span>
              </label>
            `,
          )
          .join("")}
      </div>

      <p id="validation" class="error" role="alert"></p>

      <div class="actions spread">
        <button
          class="secondary"
          id="prev"
          ${number === 1 ? "disabled" : ""}
        >
          上一題
        </button>

        <button class="primary" id="next">
          ${number === total ? "完成並對答案" : "下一題"}
        </button>
      </div>
    </section>
  `;

  app.querySelectorAll('input[name="answer"]').forEach((input) => {
    input.addEventListener("change", () => {
      const selected = [
        ...app.querySelectorAll(
          'input[name="answer"]:checked',
        ),
      ].map((item) => String(item.value));

      question.selectedOptionIds = selected;
    });
  });

  app.querySelector("#quit").addEventListener("click", () => {
    const confirmed = confirm(
      "確定要結束本次測驗？尚未送出的結果不會寫入紀錄。",
    );

    if (confirmed) {
      renderHome();
    }
  });

  app.querySelector("#prev").addEventListener("click", () => {
    quiz.currentIndex -= 1;
    renderQuestion();
  });

  app.querySelector("#next").addEventListener("click", () => {
    if (!question.selectedOptionIds.length) {
      app.querySelector("#validation").textContent =
        "請先選擇答案。";

      return;
    }

    if (number === total) {
      const unanswered = quiz.questions.filter(
        (item) => !item.selectedOptionIds.length,
      );

      if (unanswered.length) {
        app.querySelector("#validation").textContent =
          `仍有 ${unanswered.length} 題尚未作答，請返回完成。`;

        return;
      }

      finishQuiz();
      return;
    }

    quiz.currentIndex += 1;
    renderQuestion();
    recordDailyPractice();
  });
}

/* -------------------------------------------------------
 * 測驗完成
 * ----------------------------------------------------- */

function finishQuiz() {
  const results = currentQuiz.questions.map((question) => {
    const isCorrect = selectedIsCorrect(question);

    updateProgress(
      question.sourceFile,
      question,
      isCorrect,
    );

    return {
      question,
      isCorrect,
    };
  });

// 完成一次測驗後，留下當日簽到紀錄
  recordDailyPractice();

  currentQuiz.results = results;
  renderReview();
}

/* -------------------------------------------------------
 * 簽到功能
 * ----------------------------------------------------- */

function getLocalDateKey(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function recordDailyPractice() {
  const progress = loadProgress();
  const dateKey = getLocalDateKey();

  progress.practiceDates[dateKey] =
    (progress.practiceDates[dateKey] ?? 0) + 1;

  saveProgress(progress);
}

/* -------------------------------------------------------
 * 對答案頁面
 * ----------------------------------------------------- */

function renderReview() {
  const results = currentQuiz.results;

  const correctCount = results.filter(
    (result) => result.isCorrect,
  ).length;

  const wrongCount = results.length - correctCount;

  const percentage = results.length
    ? Math.round((correctCount / results.length) * 100)
    : 0;

  app.innerHTML = `
    <section class="panel">
      <h2>測驗結果</h2>

      <div class="stats">
        <div class="stat">
          <strong>${correctCount}</strong>
          <span>答對</span>
        </div>

        <div class="stat">
          <strong>${wrongCount}</strong>
          <span>答錯</span>
        </div>

        <div class="stat">
          <strong>${percentage}%</strong>
          <span>正確率</span>
        </div>
      </div>

      <p class="note">
        ${
          currentQuiz.mode === "wrong"
            ? `
              可在每題下方勾選要從本機錯題庫移除的題目，
              最後按送出。
            `
            : `
              答錯的題目已加入本機錯題紀錄。
            `
        }
      </p>

      <div id="review-list">
        ${results
          .map((result, index) => {
            const question = result.question;
            const selected = new Set(
              question.selectedOptionIds.map(String),
            );

            return `
              <article
                class="card review-item ${
                  result.isCorrect ? "correct" : "wrong"
                }"
              >
                <h3>
                  第 ${index + 1} 題：
                  ${result.isCorrect ? "答對" : "答錯"}
                </h3>

                <p>
                  ${escapeHtml(question.question)}
                </p>

                <ul class="review-options">
                  ${question.options
                    .map((option, optionIndex) => {
                      const optionId = String(option.id);

                      const classes = [
                        option.isCorrect
                          ? "correct-answer"
                          : "",
                        selected.has(optionId) &&
                        !option.isCorrect
                          ? "selected-wrong"
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ");

                      const marks = [
                        option.isCorrect
                          ? "正確答案"
                          : "",
                        selected.has(optionId)
                          ? "你的選擇"
                          : "",
                      ]
                        .filter(Boolean)
                        .join("、");

                      return `
                        <li class="${classes}">
                          <strong class="review-option-letter">${String.fromCharCode(65 + optionIndex)}.</strong>
                          ${escapeHtml(option.text)}

                          ${
                            marks
                              ? `
                                <span class="badge">
                                  ${marks}
                                </span>
                              `
                              : ""
                          }

                        </li>
                      `;
                    })
                    .join("")}
                </ul>

                <section class="answer-explanation" aria-label="本題詳解">
                  <h4>詳解</h4>
                  <p>${escapeHtml(
                    question.explanation ||
                      "本題目前尚無逐題詳解，請先依正確答案與選項標記複習。",
                  )}</p>
                  ${
                    question.chapterId
                      ? `<p class="chapter-label"><span class="badge">${escapeHtml(question.chapterId)}</span> ${escapeHtml(question.chapterName)}</p>`
                      : ""
                  }
                </section>

                ${
                  currentQuiz.mode === "wrong"
                    ? `
                      <div class="remove-box">
                        <label>
                          <input
                            type="checkbox"
                            class="remove-wrong"
                            data-file="${escapeHtml(
                              question.sourceFile,
                            )}"
                            data-id="${escapeHtml(
                              question.id,
                            )}"
                          >

                          將本題從錯題資料庫移除
                        </label>
                      </div>
                    `
                    : ""
                }
              </article>
            `;
          })
          .join("")}
      </div>

      <div class="actions spread">
        <button class="secondary" id="home">
          返回首頁
        </button>

        ${
          currentQuiz.mode === "wrong"
            ? `
              <button
                class="primary"
                id="submit-removals"
              >
                送出錯題移除設定
              </button>
            `
            : `
              <button class="primary" id="retry">
                再測一次
              </button>
            `
        }
      </div>
    </section>
  `;

  app.querySelector("#home").addEventListener("click", renderHome);

  const retryButton = app.querySelector("#retry");

  if (retryButton) {
    retryButton.addEventListener("click", () => {
      const resetQuestions = currentQuiz.questions.map(
        (question) => ({
          ...question,
          selectedOptionIds: [],
        }),
      );

      currentQuiz.questions = prepareQuestions(resetQuestions);
      currentQuiz.currentIndex = 0;

      renderQuestion();
    });
  }

  const submitButton = app.querySelector("#submit-removals");

  if (submitButton) {
    submitButton.addEventListener("click", () => {
      const checked = [
        ...app.querySelectorAll(
          ".remove-wrong:checked",
        ),
      ];

      checked.forEach((input) => {
        removeWrongRecord(
          input.dataset.file,
          input.dataset.id,
        );
      });

      alert(
        `已從錯題資料庫移除 ${checked.length} 題。`,
      );

      renderHome();
    });
  }
}

/* -------------------------------------------------------
 * 清除紀錄
 * ----------------------------------------------------- */

if (resetButton) {
  resetButton.addEventListener("click", () => {
    const confirmed = confirm(
      "確定要清除這台裝置上的全部練習紀錄？此動作無法復原。",
    );

    if (!confirmed) {
      return;
    }

    localStorage.removeItem(STORAGE_KEY);
    renderHome();
  });
}

/* -------------------------------------------------------
 * 新增統計功能
 * ----------------------------------------------------- */

async function calculateSubjectStats(subject) {
  const files = availableFiles(subject);

  if (!files.length) {
    return {
      subject,
      total: 0,
      attempted: 0,
      everCorrect: 0,
      wrong: 0,
      completionRate: 0,
      correctCoverageRate: 0,
      attemptedAccuracy: 0,
    };
  }

  const groups = await Promise.all(
    files.map((item) => loadQuestionFile(item.file)),
  );

  const questions = groups.flat();
  const progress = loadProgress();

  let attempted = 0;
  let everCorrect = 0;
  let wrong = 0;

  for (const question of questions) {
    const key = questionKey(
      question.sourceFile,
      question.id,
    );

    const record = progress.questions[key];

    if (record?.attempted) {
      attempted += 1;
    }

    if (record?.everCorrect) {
      everCorrect += 1;
    }

    if ((record?.wrongCount ?? 0) > 0) {
      wrong += 1;
    }
  }

  const total = questions.length;

  return {
    subject,
    total,
    attempted,
    everCorrect,
    wrong,

    completionRate:
      total > 0
        ? Math.round((attempted / total) * 100)
        : 0,

    correctCoverageRate:
      total > 0
        ? Math.round((everCorrect / total) * 100)
        : 0,

    attemptedAccuracy:
      attempted > 0
        ? Math.round((everCorrect / attempted) * 100)
        : 0,
  };
}

/* -------------------------------------------------------
 * 圓餅圖
 * ----------------------------------------------------- */
function progressPie(rate, centerText) {
  const safeRate = Math.max(0, Math.min(100, rate));

  return `
    <div
      class="progress-pie"
      style="--progress:${safeRate * 3.6}deg"
      role="img"
      aria-label="${safeRate}%"
    >
      <div class="progress-pie-center">
        <strong>${escapeHtml(centerText)}</strong>
      </div>
    </div>
  `;
}

/* -------------------------------------------------------
 * 建立月曆
 * ----------------------------------------------------- */

function buildCalendarData(date = new Date()) {
  const year = date.getFullYear();
  const month = date.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  const firstWeekday = firstDay.getDay();
  const totalDays = lastDay.getDate();

  return {
    year,
    month,
    firstWeekday,
    totalDays,
  };
}

function renderPracticeCalendar() {
  const progress = loadProgress();
  const calendar = buildCalendarData();

  const monthLabel =
    `${calendar.year} 年 ${calendar.month + 1} 月`;

  const weekdayLabels = [
    "日",
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
  ];

  const cells = [];

  for (let index = 0; index < calendar.firstWeekday; index += 1) {
    cells.push(`<div class="calendar-cell empty"></div>`);
  }

  for (let day = 1; day <= calendar.totalDays; day += 1) {
    const date = new Date(
      calendar.year,
      calendar.month,
      day,
    );

    const dateKey = getLocalDateKey(date);
    const practiceCount =
      progress.practiceDates?.[dateKey] ?? 0;

    cells.push(`
      <div class="calendar-cell">
        <span class="calendar-day">${day}</span>

        ${
          practiceCount > 0
            ? `
              <img
                class="calendar-stamp"
                src="./icon/yzm_icon.png"
                alt="當日已練習"
                title="當日完成 ${practiceCount} 次練習"
              >
            `
            : ""
        }

        ${
          practiceCount > 1
            ? `
              <span class="practice-count">
                ×${practiceCount}
              </span>
            `
            : ""
        }
      </div>
    `);
  }

  return `
    <section class="dashboard-section">
      <h2>每日練習簽到</h2>
      <p class="note">
        完成一次測驗並送出答案後，當天會留下簽到戳記。
      </p>

      <div class="calendar">
        <h3>${monthLabel}</h3>

        <div class="calendar-weekdays">
          ${weekdayLabels
            .map((label) => `<div>${label}</div>`)
            .join("")}
        </div>

        <div class="calendar-grid">
          ${cells.join("")}
        </div>
      </div>
    </section>
  `;
}


/* -------------------------------------------------------
 * 啟動
 * ----------------------------------------------------- */

async function init() {
  showConsentIfNeeded();

  try {
    await loadManifest();
    renderHome();
  } catch (error) {
    console.error(error);

    app.innerHTML = `
      <section class="panel">
        <h2 class="error">
          題庫目錄載入失敗
        </h2>

        <p>
          ${escapeHtml(error.message)}
        </p>

        <p>
          請確認
          <code>questions_json/manifest.json</code>
          已建立並提交至 GitHub。
        </p>
      </section>
    `;
  }
}

init();
