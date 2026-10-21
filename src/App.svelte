<script lang="ts">
  import { onMount } from 'svelte';

  type Screen = 'splash' | 'auth' | 'profile' | 'rooms' | 'waiting' | 'diagnosis' | 'loading' | 'results';
  type GradeKey = 0 | 1 | 2 | 3;

  type User = {
    id: string;
    email: string;
    password: string;
    name: string;
    nickname: string;
    grade: string;
    createdAt: number;
  };

  type Participant = {
    id: string;
    name: string;
    isAdmin: boolean;
    score: number | null;
    rank: number | null;
  };

  type Room = {
    id: string;
    name: string;
    code: string;
    ownerId: string;
    createdAt: number;
    participants: Participant[];
    status: 'waiting' | 'completed';
  };

  type DiagnosticQuestion = {
    id: string;
    label: string;
    type: 'slider' | 'radio' | 'select' | 'number';
    min?: number;
    max?: number;
    step?: number;
    value: number | string;
    options?: Array<{ value: number | string; label: string }>;
  };

  type StudentInput = {
    StudyHours: number;
    Attendance: number;
    Resources: number;
    Motivation: number;
    Internet: number;
    Gender: number;
    Age: number;
    Discussions: number;
    AssignmentCompletion: number;
    EduTech: number;
  };

  type Probability = {
    rank0: number;
    rank1: number;
    rank2: number;
    rank3: number;
  };

  type GradeResult = {
    final_grade: number;
    title: string;
    description: string;
    probabilities: Probability;
  };

  const STORAGE_KEYS = {
    users: 'student_group_demo_users',
    session: 'student_group_demo_session',
    rooms: 'student_group_demo_rooms'
  } as const;

  const gradeDescriptions: Record<GradeKey, { judge: string; title: string; description: string }> = {
    0: {
      judge: '伝説の無双キャンパスライフ',
      title: '学問を極めし絶対覇者',
      description: '圧倒的な学習習慣と完璧な自己管理です。今のペースを守れば、成績の高みを維持できます。'
    },
    1: {
      judge: '安定した優秀層',
      title: '文武両道の勝ち組',
      description: '良いバランスで学業を進めています。少しの改善でさらに安定した成績を目指せます。'
    },
    2: {
      judge: '平和主義標準層',
      title: '伸びしろ満載の中堅',
      description: '取り組み方は良いですが、習慣の維持と継続が弱い部分です。小さな改善が大きな差になります。'
    },
    3: {
      judge: '単位危険水域',
      title: '改善の余地が大きい状態',
      description: '学習習慣や課題量に改善余地があります。まずは継続しやすい目標を一つずつ立てていくと良いです。'
    }
  };

  const diagnosisQuestions: DiagnosticQuestion[] = [
    { id: 'StudyHours', label: '1週間の学習時間', type: 'slider', min: 0, max: 60, step: 1, value: 20 },
    { id: 'Attendance', label: '授業出席率', type: 'slider', min: 0, max: 100, step: 1, value: 80 },
    { id: 'AssignmentCompletion', label: '課題提出の完成度', type: 'slider', min: 0, max: 100, step: 1, value: 75 },
    { id: 'Discussions', label: '授業や話し合いへの参加度', type: 'radio', value: 1, options: [{ value: 1, label: '積極的に参加している' }, { value: 0, label: 'あまり参加していない' }] },
    { id: 'Motivation', label: '学習へのモチベーション', type: 'select', value: 2, options: [{ value: 2, label: '高い' }, { value: 1, label: '普通' }, { value: 0, label: '低い' }] },
    { id: 'Resources', label: '教材・学習リソースの活用数', type: 'slider', min: 0, max: 5, step: 1, value: 2 },
    { id: 'EduTech', label: '教育系アプリやツールの活用', type: 'radio', value: 1, options: [{ value: 1, label: '活用している' }, { value: 0, label: '使っていない' }] },
    { id: 'Internet', label: '自宅の学習環境', type: 'radio', value: 1, options: [{ value: 1, label: '快適' }, { value: 0, label: '不安がある' }] },
    { id: 'Gender', label: '性別', type: 'select', value: 0, options: [{ value: 0, label: '女性' }, { value: 1, label: '男性' }] },
    { id: 'Age', label: '年齢', type: 'number', min: 15, max: 30, value: 20 }
  ];

  const emptyRoomList: Room[] = [];

  let screen: Screen = 'splash';
  let authForm = { email: '', password: '', name: '' };
  let profileForm = { nickname: '', grade: '高校1年生' };
  let roomName = '';
  let roomCodeInput = '';
  let currentUser: User | null = null;
  let rooms: Room[] = [];
  let currentRoom: Room | null = null;
  let authError = '';
  let profileError = '';
  let roomError = '';
  let isHydrated = false;
  let diagnosisValues: Record<string, number | string> = Object.fromEntries(diagnosisQuestions.map((question) => [question.id, question.value]));
  let diagnosisIndex = 0;
  let diagnosisLoading = false;
  let diagnosisResult: GradeResult | null = null;
  let diagnosisError = '';
  let toast = '';

  const start = () => {
    if (toast) {
      setTimeout(() => {
        toast = '';
      }, 1800);
    }
  };

  const setToast = (message: string) => {
    toast = message;
    start();
  };

  const readJson = <T>(key: string, fallback: T): T => {
    try {
      const raw = localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : fallback;
    } catch {
      return fallback;
    }
  };

  const writeJson = (key: string, value: unknown) => {
    localStorage.setItem(key, JSON.stringify(value));
  };

  const getUsers = (): User[] => readJson<User[]>(STORAGE_KEYS.users, []);
  const saveUsers = (users: User[]) => writeJson(STORAGE_KEYS.users, users);
  const getRooms = (): Room[] => readJson<Room[]>(STORAGE_KEYS.rooms, emptyRoomList);
  const saveRooms = (value: Room[]) => writeJson(STORAGE_KEYS.rooms, value);

  const generateRoomCode = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 6; i += 1) {
      code += chars[Math.floor(Math.random() * chars.length)];
    }
    return code;
  };

  const getCurrentUser = (): User | null => {
    const session = readJson<{ userId: string } | null>(STORAGE_KEYS.session, null);
    if (!session) return null;
    const users = getUsers();
    return users.find((user) => user.id === session.userId) ?? null;
  };

  const buildStudentInput = (): StudentInput => {
    const getNumber = (key: string, fallback: number) => {
      const raw = diagnosisValues[key];
      const value = typeof raw === 'string' ? Number(raw) : Number(raw ?? fallback);
      return Number.isFinite(value) ? value : fallback;
    };

    return {
      StudyHours: getNumber('StudyHours', 20),
      Attendance: getNumber('Attendance', 80),
      Resources: getNumber('Resources', 2),
      Motivation: getNumber('Motivation', 2),
      Internet: getNumber('Internet', 1),
      Gender: getNumber('Gender', 0),
      Age: getNumber('Age', 20),
      Discussions: getNumber('Discussions', 1),
      AssignmentCompletion: getNumber('AssignmentCompletion', 75),
      EduTech: getNumber('EduTech', 1)
    };
  };

  const signInWithGoogle = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      setToast('Google Client ID が未設定です。 .env に VITE_GOOGLE_CLIENT_ID を設定してください。');
      return;
    }

    if (!window.google?.accounts?.id) {
      loadGoogleIdentityScript();
      setToast('Googleログインを準備しています...');
      return;
    }

    window.google.accounts.id.prompt(() => undefined);
  };

  const decodeGoogleJwt = (token: string) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const json = decodeURIComponent(
        atob(base64)
          .split('')
          .map((char) => `%${(`00${char.charCodeAt(0).toString(16)}`).slice(-2)}`)
          .join('')
      );
      return JSON.parse(json) as { email?: string; name?: string; picture?: string };
    } catch {
      return null;
    }
  };

  const handleGoogleCredentialResponse = (response: { credential?: string }) => {
    if (!response.credential) {
      setToast('Googleログインに失敗しました。');
      return;
    }

    const payload = decodeGoogleJwt(response.credential);
    if (!payload?.email) {
      setToast('Googleアカウント情報を取得できませんでした。');
      return;
    }

    let users = getUsers();
    let user = users.find((entry) => entry.email.toLowerCase() === payload.email.toLowerCase());

    if (!user) {
      user = {
        id: crypto.randomUUID(),
        email: payload.email,
        password: 'google-oauth',
        name: payload.name || payload.email.split('@')[0],
        nickname: payload.name || payload.email.split('@')[0],
        grade: '高校1年生',
        createdAt: Date.now()
      };
      users = [...users, user];
      saveUsers(users);
    }

    currentUser = user;
    persistSession(user);
    toProfileDefaults(user);
    setToast('Googleアカウントでログインしました');
    navigate(user.nickname && user.grade ? 'rooms' : 'profile');
  };

  const initializeGoogleLogin = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    const button = document.getElementById('google-login-button');
    if (!clientId || !button || !window.google?.accounts?.id) return;

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: handleGoogleCredentialResponse,
      auto_select: false,
      cancel_on_tap_outside: false
    });

    window.google.accounts.id.renderButton(button, {
      theme: 'outline',
      size: 'large',
      type: 'standard',
      text: 'continue_with',
      shape: 'pill',
      logo_alignment: 'left'
    });
  };

  const loadGoogleIdentityScript = () => {
    if (document.getElementById('google-gsi-script')) {
      setTimeout(() => initializeGoogleLogin(), 200);
      return;
    }

    const script = document.createElement('script');
    script.id = 'google-gsi-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      setTimeout(() => initializeGoogleLogin(), 150);
    };
    document.head.appendChild(script);
  };

  const persistSession = (user: User) => {
    writeJson(STORAGE_KEYS.session, { userId: user.id });
  };

  const loadPersistence = () => {
    const sessionUser = getCurrentUser();
    rooms = getRooms();

    if (sessionUser) {
      currentUser = sessionUser;
      if (sessionUser.nickname && sessionUser.grade) {
        screen = 'rooms';
      } else {
        screen = 'profile';
      }
    } else {
      screen = 'auth';
    }
  };

  const toProfileDefaults = (user: User) => {
    profileForm.nickname = user.nickname || user.name.split(' ')[0] || 'プレイヤー';
    profileForm.grade = user.grade || '高校1年生';
  };

  const navigate = (nextScreen: Screen) => {
    screen = nextScreen;
  };

  const submitAuth = () => {
    authError = '';

    if (!authForm.email.trim() || !authForm.password.trim()) {
      authError = 'メールアドレスとパスワードを入力してください。';
      return;
    }

    const users = getUsers();

    const user = users.find(
      (entry) => entry.email.toLowerCase() === authForm.email.toLowerCase() && entry.password === authForm.password
    );

    if (!user) {
      authError = 'メールアドレスまたはパスワードが正しくありません。';
      return;
    }

    currentUser = user;
    persistSession(user);
    toProfileDefaults(user);
    setToast('ログインしました');
    navigate(user.nickname && user.grade ? 'rooms' : 'profile');
  };

  const resetPassword = () => {
    if (!authForm.email.trim()) {
      authError = 'パスワード再設定にはメールアドレスが必要です。';
      return;
    }

    authError = '';
    setToast('再設定用メールを送信しました');
  };

  const saveProfile = () => {
    profileError = '';

    if (!profileForm.nickname.trim()) {
      profileError = 'ニックネームを入力してください。';
      return;
    }

    if (!currentUser) return;

    const users = getUsers().map((user) => {
      if (!currentUser) return user;
      if (user.id === currentUser.id) {
        return { ...user, nickname: profileForm.nickname.trim(), grade: profileForm.grade };
      }
      return user;
    });

    saveUsers(users);
    currentUser = { ...currentUser, nickname: profileForm.nickname.trim(), grade: profileForm.grade };
    persistSession(currentUser);
    setToast('プロフィールを保存しました');
    navigate('rooms');
  };

  const createRoom = () => {
    roomError = '';

    if (!roomName.trim()) {
      roomError = 'ルーム名を入力してください。';
      return;
    }

    if (!currentUser) return;

    const newRoom: Room = {
      id: crypto.randomUUID(),
      name: roomName.trim(),
      code: generateRoomCode(),
      ownerId: currentUser.id,
      createdAt: Date.now(),
      status: 'waiting',
      participants: [{ id: currentUser.id, name: currentUser.nickname || currentUser.name, isAdmin: true, score: null, rank: null }]
    };

    const updatedRooms = [newRoom, ...getRooms()];
    saveRooms(updatedRooms);
    rooms = updatedRooms;
    currentRoom = newRoom;
    roomName = '';
    navigate('waiting');
  };

  const joinRoom = () => {
    roomError = '';
    const code = roomCodeInput.trim().toUpperCase();
    if (!code) {
      roomError = '招待コードを入力してください。';
      return;
    }

    const user = currentUser;
    if (!user) return;

    const room = getRooms().find((entry) => entry.code === code);
    if (!room) {
      roomError = 'そのコードは存在しません。';
      return;
    }

    const alreadyJoined = room.participants.some((p) => p.id === user.id);
    if (!alreadyJoined) {
      room.participants.push({
        id: user.id,
        name: user.nickname || user.name,
        isAdmin: false,
        score: null,
        rank: null
      });
      const updatedRooms = getRooms().map((entry) => (entry.id === room.id ? room : entry));
      saveRooms(updatedRooms);
      rooms = updatedRooms;
    }

    currentRoom = room;
    roomCodeInput = '';
    navigate('waiting');
  };

  const enterRoom = (room: Room) => {
    currentRoom = room;
    navigate('waiting');
  };

  const leaveRoom = () => {
    const room = currentRoom;
    const user = currentUser;
    if (!room || !user) return;

    const updated = getRooms().map((entry) => {
      if (entry.id !== room.id) return entry;
      const participants = entry.participants.filter((participant) => participant.id !== user.id);
      return { ...entry, participants };
    });

    saveRooms(updated);
    rooms = updated;
    currentRoom = null;
    navigate('rooms');
  };

  const isAdmin = () => currentUser && currentRoom ? currentRoom.ownerId === currentUser.id : false;

  const startDiagnosis = () => {
    if (!currentRoom) return;
    diagnosisIndex = 0;
    diagnosisResult = null;
    diagnosisValues = Object.fromEntries(diagnosisQuestions.map((question) => [question.id, question.value]));
    navigate('diagnosis');
  };

  const getNumericValue = (id: string) => {
    const value = diagnosisValues[id];
    return typeof value === 'string' ? Number(value) : value;
  };

  const probabilityOrder: Array<{ key: keyof Probability; label: string }> = [
    { key: 'rank0', label: 'ランク0' },
    { key: 'rank1', label: 'ランク1' },
    { key: 'rank2', label: 'ランク2' },
    { key: 'rank3', label: 'ランク3' }
  ];

  const getGradeJudge = (grade: number) => gradeDescriptions[grade as GradeKey].judge;

  const getProbabilityValue = (key: keyof Probability, result: GradeResult | null) => {
    if (!result) return 0;
    return result.probabilities[key] ?? 0;
  };

  const handleOptionChange = (event: Event, key: string) => {
    const target = event.currentTarget as HTMLInputElement;
    diagnosisValues[key] = Number(target.value);
  };

  const handleNumberChange = (event: Event, key: string) => {
    const target = event.currentTarget as HTMLInputElement;
    diagnosisValues[key] = Number(target.value);
  };

  const currentQuestion = diagnosisQuestions[diagnosisIndex];

  const nextQuestion = () => {
    if (diagnosisIndex < diagnosisQuestions.length - 1) {
      diagnosisIndex += 1;
    }
  };

  const previousQuestion = () => {
    if (diagnosisIndex > 0) {
      diagnosisIndex -= 1;
    }
  };

  const submitDiagnosis = async () => {
    if (!currentUser || !currentRoom) return;
    diagnosisLoading = true;
    diagnosisError = '';
    navigate('loading');

    try {
      const response = await fetch('http://127.0.0.1:8000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildStudentInput())
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await response.json();
      const rankKey = Number(payload.final_grade) as GradeKey;
      const info = gradeDescriptions[rankKey];

      diagnosisResult = {
        final_grade: Number(payload.final_grade),
        title: info.title,
        description: info.description,
        probabilities: payload.probabilities
      };

      const updatedRooms = getRooms().map((room) => {
        if (!currentRoom || room.id !== currentRoom.id) return room;

        const updatedParticipants = room.participants.map((participant) => {
          if (!currentUser) return participant;
          if (participant.id !== currentUser.id) return participant;
          return { ...participant, score: Number(payload.final_grade), rank: null };
        });

        return { ...room, participants: updatedParticipants };
      });

      saveRooms(updatedRooms);
      rooms = updatedRooms;
      currentRoom = updatedRooms.find((room) => room.id === currentRoom?.id) ?? currentRoom;
      navigate('results');
    } catch (error) {
      diagnosisError = '診断処理に失敗しました。通信環境を確認して再試行してください。';
      navigate('diagnosis');
      console.error(error);
    } finally {
      diagnosisLoading = false;
    }
  };

  const resetForReDiagnosis = () => {
    diagnosisIndex = 0;
    diagnosisValues = Object.fromEntries(diagnosisQuestions.map((question) => [question.id, question.value]));
    diagnosisResult = null;
    navigate('diagnosis');
  };

  const goBackToRoom = () => {
    currentRoom = currentRoom ?? rooms[0] ?? null;
    navigate('waiting');
  };

  const logout = () => {
    currentUser = null;
    currentRoom = null;
    localStorage.removeItem(STORAGE_KEYS.session);
    toast = 'ログアウトしました';
    setTimeout(() => {
      navigate('auth');
    }, 250);
  };

  onMount(() => {
    isHydrated = true;
    loadGoogleIdentityScript();
    const sessionUser = getCurrentUser();
    const storedRooms = getRooms();
    rooms = storedRooms;

    if (sessionUser) {
      currentUser = sessionUser;
      if (sessionUser.nickname && sessionUser.grade) {
        navigate('rooms');
      } else {
        toProfileDefaults(sessionUser);
        navigate('profile');
      }
      return;
    }

    setTimeout(() => {
      navigate('auth');
    }, 1200);
  });

  $: progressRate = ((diagnosisIndex + 1) / diagnosisQuestions.length) * 100;
  $: ranking = currentRoom
    ? [...currentRoom.participants].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    : [];
  $: mostConcerned = ranking.length > 0 ? ranking[ranking.length - 1] : null;
  $: if (currentUser && currentUser.nickname && currentUser.grade && screen === 'splash' && isHydrated) {
    // no-op: keep splash behavior simple
  }
</script>

<svelte:head>
  <title>Group Grade Studio</title>
</svelte:head>

{#if screen === 'splash'}
  <div class="screen splash-screen">
    <div class="splash-card">
      <div class="logo-badge">AI</div>
      <p class="eyebrow">STUDENT GROUP DIAGNOSTIC</p>
      <h1>Grade Studio</h1>
      <p class="tagline">友だちと一緒に、学習習慣を見える化しよう</p>
      <div class="loader"><span></span></div>
    </div>
  </div>
{:else if screen === 'auth'}
  <div class="screen auth-screen">
    <div class="phone-shell">
      <div class="topbar-simple">
        <div class="brand-inline"><span>AI</span>Grade Studio</div>
      </div>
      <div class="auth-card card">
        <p class="eyebrow">WELCOME</p>
        <h2>Googleでログイン</h2>

        <div class="oauth-stack">
          <button class="primary-button full" on:click={signInWithGoogle} type="button">Googleで続ける</button>
          <div id="google-login-button"></div>
        </div>

        <p class="auth-hint">Googleアカウントを使って、すぐにグループ診断を始められます。</p>
      </div>
    </div>
  </div>
{:else if screen === 'profile'}
  <div class="screen mobile-screen">
    <div class="phone-shell small-gap">
      <header class="mobile-header">
        <div>
          <p class="eyebrow">PROFILE</p>
          <h2>基本情報を設定</h2>
        </div>
      </header>

      <div class="card form-card">
        <div class="field-stack">
          <label>
            <span>ニックネーム</span>
            <input bind:value={profileForm.nickname} type="text" placeholder="例: しおり" />
          </label>

          <label>
            <span>学年</span>
            <select bind:value={profileForm.grade}>
              <option value="高校1年生">高校1年生</option>
              <option value="高校2年生">高校2年生</option>
              <option value="高校3年生">高校3年生</option>
              <option value="大学1年生">大学1年生</option>
              <option value="大学2年生">大学2年生</option>
              <option value="大学3年生">大学3年生</option>
              <option value="大学4年生">大学4年生</option>
            </select>
          </label>
        </div>

        {#if profileError}
          <p class="error-text">{profileError}</p>
        {/if}
      </div>

      <div class="bottom-bar">
        <button class="primary-button full" on:click={saveProfile} type="button">プロフィールを保存</button>
      </div>
    </div>
  </div>
{:else if screen === 'rooms'}
  <div class="screen mobile-screen">
    <div class="phone-shell small-gap">
      <header class="mobile-header room-header">
        <div>
          <p class="eyebrow">ROOMS</p>
          <h2>ルーム一覧</h2>
        </div>
        <button class="menu-button" on:click={logout} type="button">ログアウト</button>
      </header>

      <div class="card create-room-card">
        <label>
          <span>新しいルーム名</span>
          <input bind:value={roomName} placeholder="例: しゅわしゅわ勉強会" type="text" />
        </label>
        <button class="primary-button full" on:click={createRoom} type="button">ルームを作成</button>
      </div>

      <div class="card join-card">
        <label>
          <span>招待コードで参加</span>
          <input bind:value={roomCodeInput} maxlength="6" placeholder="ABC123" type="text" />
        </label>
        <button class="secondary-button full" on:click={joinRoom} type="button">コードで参加</button>
      </div>

      {#if roomError}
        <p class="error-text">{roomError}</p>
      {/if}

      <section class="list-section">
        <div class="section-head">
          <h3>参加中のルーム</h3>
        </div>

        {#if rooms.length === 0}
          <div class="empty-card">まだルームがありません。新しく作成しましょう。</div>
        {:else}
          {#each rooms as room}
            <button class="room-card" on:click={() => enterRoom(room)} type="button">
              <div class="room-card-top">
                <div>
                  <strong>{room.name}</strong>
                  <span>{room.code}</span>
                </div>
                <span class="pill">{room.participants.length}人</span>
              </div>
              <div class="room-meta">
                <span>{room.status === 'waiting' ? '待機中' : '診断完了'}</span>
                <span>{room.participants[0]?.name ?? '管理者'}</span>
              </div>
            </button>
          {/each}
        {/if}
      </section>
    </div>
  </div>
{:else if screen === 'waiting'}
  <div class="screen mobile-screen">
    <div class="phone-shell small-gap">
      <header class="mobile-header room-header">
        <div>
          <p class="eyebrow">WAITING ROOM</p>
          <h2>{currentRoom?.name ?? 'ルーム'}</h2>
        </div>
        <button class="menu-button" on:click={leaveRoom} type="button">退出</button>
      </header>

      <div class="card room-info-card">
        <div class="info-row">
          <span>コード</span>
          <strong>{currentRoom?.code ?? '---'}</strong>
        </div>
        <div class="info-row">
          <span>参加人数</span>
          <strong>{currentRoom?.participants.length ?? 0}人</strong>
        </div>
      </div>

      <div class="participant-list card">
        <div class="section-head">
          <h3>参加者</h3>
        </div>
        {#each currentRoom?.participants ?? [] as participant}
          <div class="participant-item">
            <div class="avatar">{participant.name.slice(0, 1)}</div>
            <div class="participant-meta">
              <strong>{participant.name}</strong>
              <span>{participant.isAdmin ? '管理者' : '参加者'}</span>
            </div>
            {#if participant.isAdmin}
              <span class="badge admin-badge">Admin</span>
            {/if}
          </div>
        {/each}
      </div>

      <div class="bottom-bar">
        <button
          class="primary-button full"
          on:click={startDiagnosis}
          type="button"
          disabled={!isAdmin()}
          class:disabled-button={!isAdmin()}
        >
          {isAdmin() ? '診断を開始' : '管理者が開始します'}
        </button>
      </div>
    </div>
  </div>
{:else if screen === 'diagnosis'}
  <div class="screen mobile-screen">
    <div class="phone-shell small-gap">
      <header class="mobile-header">
        <div>
          <p class="eyebrow">DIAGNOSIS</p>
          <h2>個人診断</h2>
        </div>
      </header>

      <div class="progress-card card">
        <div class="progress-top">
          <span>{diagnosisIndex + 1}/{diagnosisQuestions.length}</span>
          <span>{Math.round(progressRate)}%</span>
        </div>
        <div class="progress-bar">
          <div style={`width: ${progressRate}%`}></div>
        </div>
      </div>

      <div class="card question-card">
        <h3>{currentQuestion.label}</h3>

        {#if currentQuestion.type === 'slider'}
          <input
            type="range"
            min={currentQuestion.min}
            max={currentQuestion.max}
            step={currentQuestion.step}
            bind:value={diagnosisValues[currentQuestion.id]}
          />
          <div class="range-value">{diagnosisValues[currentQuestion.id]} / {currentQuestion.max}</div>
        {:else if currentQuestion.type === 'radio'}
          <div class="choice-list">
            {#each currentQuestion.options ?? [] as option}
              <label class="choice-item">
                <input
                  type="radio"
                  name={currentQuestion.id}
                  value={option.value}
                  checked={String(diagnosisValues[currentQuestion.id]) === String(option.value)}
                  on:change={(event) => handleOptionChange(event, currentQuestion.id)}
                />
                <span>{option.label}</span>
              </label>
            {/each}
          </div>
        {:else if currentQuestion.type === 'select'}
          <select bind:value={diagnosisValues[currentQuestion.id]}>
            {#each currentQuestion.options ?? [] as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        {:else}
          <input type="number" min={currentQuestion.min ?? 0} max={currentQuestion.max ?? 100} bind:value={diagnosisValues[currentQuestion.id]} />
        {/if}
      </div>

      <div class="bottom-nav">
        <button class="ghost-button" on:click={previousQuestion} disabled={diagnosisIndex === 0} type="button">戻る</button>
        {#if diagnosisIndex < diagnosisQuestions.length - 1}
          <button class="primary-button" on:click={nextQuestion} type="button">次へ</button>
        {:else}
          <button class="primary-button" on:click={submitDiagnosis} type="button">結果を見る</button>
        {/if}
      </div>
    </div>
  </div>
{:else if screen === 'loading'}
  <div class="screen loading-screen">
    <div class="loading-card card">
      <div class="spinner"></div>
      <h2>回答を分析しています</h2>
      <p>診断結果を準備しています。しばらくお待ちください。</p>
      {#if diagnosisError}
        <p class="error-text">{diagnosisError}</p>
      {/if}
    </div>
  </div>
{:else if screen === 'results'}
  <div class="screen mobile-screen">
    <div class="phone-shell small-gap">
      <header class="mobile-header">
        <div>
          <p class="eyebrow">RESULT</p>
          <h2>診断結果</h2>
        </div>
      </header>

      {#if diagnosisResult}
        <div class="card result-hero">
          <div class="result-badge">スコア {diagnosisResult.final_grade}</div>
          <h3>{diagnosisResult.title}</h3>
          <p>{getGradeJudge(Number(diagnosisResult.final_grade))}</p>
          <small>{diagnosisResult.description}</small>
        </div>

        <div class="probability-grid">
          {#each probabilityOrder as item}
            <div class="prob-card">
              <span>{item.label}</span>
              <strong>{getProbabilityValue(item.key, diagnosisResult).toFixed(1)}%</strong>
            </div>
          {/each}
        </div>
      {/if}

      <div class="card ranking-card">
        <div class="section-head">
          <h3>全体ランキング</h3>
        </div>
        {#if ranking.length > 0}
          {#each ranking as entry, index}
            <div class="ranking-row">
              <div class="rank-mark">#{index + 1}</div>
              <div class="ranking-user">
                <strong>{entry.name}</strong>
                <span>{entry.score ?? 0} pt</span>
              </div>
              <div class="mini-progress">
                <div style={`width: ${((entry.score ?? 0) / 3) * 100}%`}></div>
              </div>
            </div>
          {/each}
        {/if}
      </div>

      {#if mostConcerned}
        <div class="card attention-card">
          <p class="eyebrow">ATTENTION</p>
          <h3>今回の注意が必要な人</h3>
          <strong>{mostConcerned.name}</strong>
          <p>成績の伸びしろが大きく、改善の余地が残っています。メンタルと習慣を整えると一気に安定します。</p>
        </div>
      {/if}

      <div class="bottom-nav result-actions">
        <button class="ghost-button" on:click={goBackToRoom} type="button">ルームへ戻る</button>
        <button class="primary-button" on:click={resetForReDiagnosis} type="button">再診断</button>
      </div>
    </div>
  </div>
{/if}

{#if toast}
  <div class="toast">{toast}</div>
{/if}

<style>
  :global(html, body) {
    margin: 0;
    min-height: 100%;
    background: linear-gradient(180deg, #f4f8ff 0%, #edf3ff 100%);
    font-family: 'Segoe UI', 'Hiragino Sans', 'Noto Sans JP', sans-serif;
    color: #14233d;
  }

  :global(*) {
    box-sizing: border-box;
  }

  button,
  input,
  select {
    font: inherit;
  }

  .screen {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 18px;
  }

  .mobile-screen,
  .auth-screen {
    width: 100%;
  }

  .phone-shell {
    width: min(100%, 460px);
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .small-gap {
    gap: 12px;
  }

  .card {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(93, 120, 186, 0.14);
    border-radius: 22px;
    box-shadow: 0 18px 30px rgba(38, 62, 111, 0.08);
    padding: 18px;
  }

  .splash-screen {
    background: radial-gradient(circle at top, rgba(116, 159, 255, 0.3), transparent 30%), #eef4ff;
  }

  .splash-card {
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(116, 159, 255, 0.18);
    border-radius: 28px;
    padding: 32px 24px;
    width: min(100%, 360px);
    text-align: center;
    box-shadow: 0 24px 40px rgba(39, 88, 180, 0.12);
  }

  .logo-badge {
    width: 72px;
    height: 72px;
    margin: 0 auto 18px;
    border-radius: 22px;
    display: grid;
    place-items: center;
    font-weight: 800;
    color: white;
    background: linear-gradient(135deg, #2d74ff, #6bb4ff);
    box-shadow: 0 12px 26px rgba(45, 116, 255, 0.28);
  }

  .eyebrow {
    margin: 0 0 8px;
    color: #4e73d2;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  h1,
  h2,
  h3,
  p {
    margin: 0;
  }

  h1 {
    font-size: clamp(2.2rem, 9vw, 3rem);
    letter-spacing: -0.06em;
  }

  h2 {
    font-size: 1.7rem;
    letter-spacing: -0.04em;
  }

  .tagline {
    margin-top: 12px;
    color: #496692;
    line-height: 1.6;
  }

  .loader {
    width: 104px;
    height: 8px;
    background: rgba(98, 149, 255, 0.12);
    border-radius: 999px;
    margin: 26px auto 0;
    overflow: hidden;
    position: relative;
  }

  .loader span {
    display: block;
    width: 32%;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #2d74ff, #77beff);
    animation: loading 1.3s ease-in-out infinite alternate;
  }

  @keyframes loading {
    0% { transform: translateX(-10%); }
    100% { transform: translateX(220%); }
  }

  .topbar-simple,
  .mobile-header,
  .room-header,
  .section-head,
  .progress-top,
  .info-row,
  .room-card-top,
  .room-meta,
  .participant-item,
  .ranking-row,
  .bottom-nav,
  .bottom-bar,
  .stack-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .brand-inline {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    color: #1c3e7b;
  }

  .brand-inline span {
    width: 26px;
    height: 26px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #2d74ff, #74baff);
    color: white;
    font-size: 0.7rem;
  }

  .auth-card,
  .form-card,
  .create-room-card,
  .join-card,
  .participant-list,
  .progress-card,
  .question-card,
  .ranking-card,
  .room-info-card,
  .attention-card,
  .result-hero {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .field-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 8px;
    color: #1d3358;
    font-weight: 600;
    font-size: 0.95rem;
  }

  input,
  select {
    width: 100%;
    border: 1px solid rgba(115, 143, 193, 0.25);
    border-radius: 14px;
    background: #f8fbff;
    min-height: 48px;
    padding: 12px 14px;
    color: #14233d;
  }

  input:focus,
  select:focus {
    outline: 2px solid rgba(75, 117, 222, 0.18);
    border-color: rgba(76, 120, 223, 0.55);
  }

  .oauth-stack,
  .stack-actions,
  .bottom-nav,
  .bottom-bar {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .auth-hint {
    color: #5d759f;
    font-size: 0.88rem;
    line-height: 1.6;
    text-align: center;
  }

  .divider {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6b7fa5;
    font-size: 0.8rem;
    margin: 4px 0;
  }

  .divider::before,
  .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(110, 132, 182, 0.18);
  }

  .divider span {
    padding: 0 10px;
  }

  .primary-button,
  .secondary-button,
  .ghost-button,
  .menu-button,
  .text-button,
  .room-card {
    border: none;
    border-radius: 14px;
    min-height: 48px;
    cursor: pointer;
    transition: transform 0.2s ease, opacity 0.2s ease;
  }

  .primary-button,
  .secondary-button,
  .ghost-button,
  .menu-button {
    padding: 0 16px;
    font-weight: 700;
  }

  .primary-button {
    background: linear-gradient(135deg, #2d74ff, #6fade8);
    color: white;
    box-shadow: 0 14px 24px rgba(45, 116, 255, 0.2);
  }

  .secondary-button {
    background: #edf4ff;
    color: #234799;
    border: 1px solid rgba(97, 129, 222, 0.16);
  }

  .ghost-button,
  .menu-button,
  .text-button {
    background: transparent;
    color: #2a4e9d;
  }

  .full {
    width: 100%;
  }

  .error-text {
    color: #d14343;
    font-size: 0.85rem;
    font-weight: 600;
    line-height: 1.5;
    margin: 0;
  }

  .list-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 4px;
  }

  .empty-card {
    padding: 18px;
    border-radius: 18px;
    background: #f4f8ff;
    color: #4c6899;
    border: 1px dashed rgba(110, 133, 182, 0.26);
  }

  .room-card {
    width: 100%;
    text-align: left;
    background: #f9fbff;
    border: 1px solid rgba(101, 123, 184, 0.16);
    padding: 14px 16px;
    box-shadow: 0 8px 18px rgba(27, 44, 75, 0.02);
  }

  .room-card strong {
    display: block;
    color: #18315d;
    font-size: 1.05rem;
  }

  .room-card span {
    color: #56709a;
    font-size: 0.82rem;
  }

  .pill,
  .badge,
  .result-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 6px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
  }

  .pill {
    background: rgba(59, 129, 255, 0.12);
    color: #2354bf;
  }

  .info-row {
    font-size: 0.95rem;
    color: #425d8a;
  }

  .participant-list {
    gap: 10px;
  }

  .participant-item {
    background: #f6f9ff;
    border: 1px solid rgba(109, 133, 184, 0.12);
    border-radius: 14px;
    padding: 10px 12px;
    justify-content: flex-start;
  }

  .avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #2d74ff, #77c4ff);
    color: white;
    font-weight: 700;
  }

  .participant-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
  }

  .participant-meta span {
    color: #6b7fa5;
    font-size: 0.76rem;
  }

  .admin-badge {
    background: rgba(76, 195, 143, 0.14);
    color: #0a8d62;
  }

  .progress-card {
    gap: 10px;
  }

  .progress-bar {
    width: 100%;
    height: 10px;
    background: rgba(93, 126, 196, 0.1);
    border-radius: 999px;
    overflow: hidden;
  }

  .progress-bar div,
  .mini-progress div {
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #2d74ff, #72cbff);
  }

  .question-card {
    min-height: 220px;
    justify-content: center;
  }

  .choice-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .choice-item {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid rgba(99, 127, 196, 0.16);
    border-radius: 14px;
    padding: 10px 12px;
    background: #f7faff;
  }

  .choice-item input {
    width: 18px;
    min-height: 18px;
  }

  .range-value {
    text-align: center;
    color: #375fa6;
    font-weight: 700;
  }

  .loading-screen {
    background: linear-gradient(180deg, rgba(84, 136, 255, 0.1), rgba(240, 245, 255, 0.9));
  }

  .loading-card {
    width: min(100%, 340px);
    text-align: center;
    padding: 30px 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
  }

  .spinner {
    width: 58px;
    height: 58px;
    border-radius: 50%;
    border: 5px solid rgba(96, 136, 222, 0.18);
    border-top-color: #2d74ff;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .result-hero {
    background: linear-gradient(180deg, #eff6ff, #f8fbff);
  }

  .result-badge {
    width: fit-content;
    background: rgba(45, 116, 255, 0.12);
    color: #1f58ce;
  }

  .result-hero h3 {
    font-size: 1.5rem;
  }

  .result-hero small {
    color: #56709a;
    line-height: 1.6;
  }

  .probability-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .prob-card {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 12px;
    border-radius: 14px;
    background: #f6f9ff;
    border: 1px solid rgba(94, 123, 186, 0.12);
  }

  .prob-card span {
    color: #4f6c9d;
    font-size: 0.8rem;
  }

  .prob-card strong {
    font-size: 1.15rem;
  }

  .ranking-row {
    display: grid;
    grid-template-columns: 52px 1fr 90px;
    gap: 10px;
    align-items: center;
    background: #f7faff;
    border: 1px solid rgba(96, 129, 197, 0.14);
    border-radius: 12px;
    padding: 10px 12px;
  }

  .rank-mark {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: rgba(45, 116, 255, 0.08);
    color: #1a53b8;
    font-weight: 800;
  }

  .ranking-user {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .ranking-user span {
    color: #6280b0;
    font-size: 0.8rem;
  }

  .mini-progress {
    height: 9px;
    border-radius: 999px;
    background: rgba(93, 126, 196, 0.12);
    overflow: hidden;
  }

  .attention-card strong {
    font-size: 1.2rem;
  }

  .disabled-button {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: none;
  }

  .toast {
    position: fixed;
    right: 18px;
    bottom: 18px;
    background: rgba(22, 33, 55, 0.92);
    color: white;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 0.84rem;
    box-shadow: 0 16px 28px rgba(16, 23, 42, 0.2);
  }

  @media (min-width: 768px) {
    .phone-shell {
      width: min(100%, 520px);
    }

    .screen {
      padding: 28px;
    }
  }
</style>
