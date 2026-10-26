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
    riskScore: number | null;
    prob3: number | null;
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
      judge: 'ランク 0: スーパーエリートワークマン',
      title: 'スーパーエリートワークマン',
      description: '圧倒的な作業量と出席率。グループを牽引する絶対的エースです。'
    },
    1: {
      judge: 'ランク 1: 地雷回避・安定グループワーク',
      title: '地雷回避・安定グループワーク',
      description: 'バランスよく作業を進めています。地雷をうまく回避できています。'
    },
    2: {
      judge: 'ランク 2: 地雷踏みかけ・爆発寸前',
      title: '地雷踏みかけ・爆発寸前',
      description: '取り組み方は悪くないですが、モチベーションや進捗維持が危うい状態です。'
    },
    3: {
      judge: 'ランク 3: 【地雷確定】グループ全員に謝礼金レベル',
      title: '【地雷確定】グループ全員に謝礼金レベル',
      description: '作業時間や課題量に深刻な課題があります。直ちに生活習慣を見直してください。'
    }
  };

  const diagnosisQuestions: DiagnosticQuestion[] = [
    { id: 'StudyHours', label: '1週間の作業時間 (時間)', type: 'slider', min: 0, max: 60, step: 1, value: 20 },
    { id: 'Attendance', label: 'グループワークの出席率 (%)', type: 'slider', min: 0, max: 100, step: 1, value: 80 },
    { id: 'AssignmentCompletion', label: '課題の完了度 (%)', type: 'slider', min: 0, max: 100, step: 1, value: 75 },
    { id: 'Discussions', label: 'ディスカッションへの積極参加', type: 'radio', value: 1, options: [{ value: 1, label: '参加している' }, { value: 0, label: 'あまり参加していない' }] },
    { id: 'Motivation', label: '作業へのモチベーション', type: 'select', value: 2, options: [{ value: 2, label: '2: 高い' }, { value: 1, label: '1: 普通' }, { value: 0, label: '0: 低い' }] },
    { id: 'Resources', label: '活用している教材・リソース数', type: 'slider', min: 0, max: 5, step: 1, value: 2 },
    { id: 'EduTech', label: 'EdTechツール（AI等）の活用', type: 'radio', value: 1, options: [{ value: 1, label: '活用している' }, { value: 0, label: '使っていない' }] },
    { id: 'Internet', label: '自宅のネット環境', type: 'radio', value: 1, options: [{ value: 1, label: '快適' }, { value: 0, label: '不安あり' }] },
    { id: 'Gender', label: '性別', type: 'select', value: 0, options: [{ value: 0, label: '女性' }, { value: 1, label: '男性' }] },
    { id: 'Age', label: '年齢', type: 'number', min: 15, max: 30, value: 20 }
  ];

  const emptyRoomList: Room[] = [];

  let screen: Screen = 'rooms';
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

  let isGoogleReady = false;

  const ensureGoogleInitialized = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId || !window.google?.accounts?.id) return false;
    try {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
      });
      isGoogleReady = true;
      return true;
    } catch (e) {
      console.warn('Google Auth Init error:', e);
      return false;
    }
  };

  const renderGoogleButton = (node: HTMLElement) => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      console.warn('VITE_GOOGLE_CLIENT_ID is not configured');
      return;
    }

    const tryRender = () => {
      if (!window.google?.accounts?.id) return false;
      ensureGoogleInitialized();
      try {
        node.innerHTML = '';
        window.google.accounts.id.renderButton(node, {
          theme: 'outline',
          size: 'large',
          type: 'standard',
          text: 'continue_with',
          shape: 'pill',
          logo_alignment: 'left',
          width: 280
        });
        return true;
      } catch (err) {
        console.error('Failed to render Google button:', err);
        return false;
      }
    };

    if (!tryRender()) {
      let attempts = 0;
      const timer = setInterval(() => {
        attempts += 1;
        if (tryRender() || attempts > 20) {
          clearInterval(timer);
        }
      }, 250);
    }
  };

  const signInWithGoogle = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      setToast('Google Client ID が未設定です。.env に VITE_GOOGLE_CLIENT_ID を設定してください。');
      return;
    }

    if (!window.google?.accounts?.id) {
      loadGoogleIdentityScript();
      setToast('Google認証を読み込み中です。少々お待ちください...');
      return;
    }

    ensureGoogleInitialized();
    try {
      window.google.accounts.id.prompt((notification: any) => {
        if (notification?.isNotDisplayed?.() || notification?.isSkippedMoment?.()) {
          setToast('Googleボタンをクリックしてログインしてください。');
        }
      });
    } catch {
      setToast('Googleログインボタンをクリックしてください。');
    }
  };

  const loginAsGuest = () => {
    const guestUser: User = {
      id: crypto.randomUUID(),
      email: `guest_${Math.floor(Math.random() * 9000 + 1000)}@example.com`,
      password: 'guest-login',
      name: 'テストプレイヤー',
      nickname: 'テストプレイヤー',
      grade: '大学2年生',
      createdAt: Date.now()
    };
    let users = getUsers();
    users = [...users, guestUser];
    saveUsers(users);
    currentUser = guestUser;
    persistSession(guestUser);
    toProfileDefaults(guestUser);
    setToast('ゲストとしてログインしました');
    navigate('rooms');
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
        grade: '大学1年生',
        createdAt: Date.now()
      };
      users = [...users, user];
      saveUsers(users);
    }

    currentUser = user;
    persistSession(user);
    toProfileDefaults(user);
    setToast(`${user.name}さん、ようこそ！`);
    navigate(user.nickname && user.grade ? 'rooms' : 'profile');
  };

  const loadGoogleIdentityScript = () => {
    if (window.google?.accounts?.id) {
      ensureGoogleInitialized();
      return;
    }

    if (document.getElementById('google-gsi-script')) {
      return;
    }

    const script = document.createElement('script');
    script.id = 'google-gsi-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      ensureGoogleInitialized();
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

  $: currentQuestion = diagnosisQuestions[diagnosisIndex];

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

  const SONY_API_KEY = 'df4d195d-dfa9-4e10-b515-77e15096d492';
  const SONY_API_URL = 'https://user-api.predictionone.sony.biz/v1/groups/qejw062trt0qwwav/classifiers/quipaioomqira6hd/inference';

  const predictDirectlyFromSony = async (input: StudentInput): Promise<{ final_grade: number; probabilities: Probability }> => {
    const csvContent = [
      'StudyHours,Attendance,Resources,Motivation,Internet,Gender,Age,Discussions,AssignmentCompletion,EduTech',
      `${input.StudyHours},${input.Attendance},${input.Resources},${input.Motivation},${input.Internet},${input.Gender},${input.Age},${input.Discussions},${input.AssignmentCompletion},${input.EduTech}`
    ].join('\n') + '\n';

    const encodedData = btoa(unescape(encodeURIComponent(csvContent)));
    const response = await fetch(SONY_API_URL, {
      method: 'POST',
      headers: {
        'x-api-key': SONY_API_KEY,
        'content-type': 'application/json; charset=utf-8'
      },
      body: JSON.stringify({
        inputs: [
          { name: 'pr', type: 'csv', data: encodedData },
          { name: 'ar', type: 'boolean', data: false },
          { name: 'ad', type: 'boolean', data: true },
          { name: 'nc', type: 'boolean', data: false }
        ]
      })
    });

    if (!response.ok) {
      throw new Error(`Sony API HTTP ${response.status}`);
    }

    const json = await response.json();
    const output = (json.outputs || []).find((item: any) => item.name === 'prediction_valid.csv');
    if (!output) {
      throw new Error('prediction_valid.csv not found');
    }

    const decodedCsv = decodeURIComponent(escape(atob(output.data)));
    const lines = decodedCsv.trim().split('\n');
    const cols = lines[1].split(',');

    return {
      final_grade: parseInt(cols[1], 10),
      probabilities: {
        rank0: parseFloat(cols[2]) * 100,
        rank1: parseFloat(cols[3]) * 100,
        rank2: parseFloat(cols[4]) * 100,
        rank3: parseFloat(cols[5]) * 100
      }
    };
  };

  const submitDiagnosis = async () => {
    if (!currentUser || !currentRoom) return;
    diagnosisLoading = true;
    diagnosisError = '';
    navigate('loading');

    try {
      let payload: { final_grade: number; probabilities: Probability };
      const studentInput = buildStudentInput();

      try {
        const response = await fetch('http://127.0.0.1:8000/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(studentInput)
        });

        if (response.ok) {
          payload = await response.json();
        } else {
          payload = await predictDirectlyFromSony(studentInput);
        }
      } catch {
        // バックエンドが未起動の場合は直接Sony Prediction One APIへ
        payload = await predictDirectlyFromSony(studentInput);
      }

      const rankKey = Number(payload.final_grade) as GradeKey;
      const info = gradeDescriptions[rankKey];
      const riskScore = payload.final_grade * 100 + (payload.probabilities?.rank3 ?? 0);

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
          return {
            ...participant,
            score: Number(payload.final_grade),
            riskScore: riskScore,
            prob3: payload.probabilities?.rank3 ?? 0,
            rank: null
          };
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

    const goHome = () => {
    currentRoom = null;
    navigate('rooms');
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
    const sessionUser = getCurrentUser();
    if (sessionUser) {
      currentUser = sessionUser;
      rooms = getRooms();
      navigate('rooms');
    } else {
      // セッションなし → Google ログイン画面へ
      navigate('auth');
    }
  });

  $: progressRate = ((diagnosisIndex + 1) / diagnosisQuestions.length) * 100;
  $: ranking = currentRoom
    ? [...currentRoom.participants].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    : [];
  $: maxRiskPlayer = currentRoom
    ? [...currentRoom.participants]
        .filter((p) => p.riskScore !== null && p.riskScore !== undefined)
        .sort((a, b) => (b.riskScore ?? 0) - (a.riskScore ?? 0))[0] ?? null
    : null;
  $: mostConcerned = ranking.length > 0 ? ranking[ranking.length - 1] : null;
  $: if (currentUser && currentUser.nickname && currentUser.grade && screen === 'splash' && isHydrated) {
    // no-op: keep splash behavior simple
  }
</script>

<svelte:head>
  <title>グループ診断</title>
</svelte:head>

{#if screen === 'auth'}
  <div class="screen">
    <div class="phone-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">LOGIN</p>
          <h2>ログイン</h2>
        </div>
      </header>
      <div class="content-scroll-area">
        <div class="card" style="margin-top:2rem; text-align:center;">
          <p style="margin-bottom:1.5rem; color:#555;">Googleアカウントでサインインしてください</p>
          <div use:renderGoogleButton style="display:flex; justify-content:center;"></div>
          <hr style="margin: 1.5rem 0; border:none; border-top:1px solid #e0e0e0;" />
          <button class="secondary-button full" on:click={loginAsGuest} type="button">ゲストとして続ける</button>
        </div>
      </div>
    </div>
  </div>
{:else if screen === 'rooms'}
  <div class="screen">
    <div class="phone-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">HOME</p>
          <h2>ホーム</h2>
        </div>
        <button class="ghost-button small-btn" on:click={logout} type="button">ログアウト</button>
      </header>

      <div class="content-scroll-area">
        <div class="card form-card">
          <label>
            <span>ルームを作成して開始</span>
            <input bind:value={roomName} placeholder="ルーム名を入力（例: 班A）" type="text" />
          </label>
          <button class="primary-button full" on:click={createRoom} type="button">ルームを作成</button>
        </div>

        <div class="card form-card compact-card">
          <label>
            <span>招待コードで参加</span>
            <div class="inline-input-group">
              <input bind:value={roomCodeInput} maxlength="6" placeholder="コード (6桁)" type="text" />
              <button class="secondary-button" on:click={joinRoom} type="button">参加</button>
            </div>
          </label>
        </div>

        {#if roomError}
          <p class="error-text">{roomError}</p>
        {/if}

        <!-- 偽サイト風の怪しい広告バナー（絵文字なし・クリーン） -->
        <a 
          href="https://youtu.be/-ZGlaAxB7nI?si=PRc-BstyAs7hdJ6F" 
          target="_blank" 
          rel="noopener noreferrer" 
          class="fake-ad-card"
        >
          <div class="ad-top-bar">
            <span class="ad-badge">[PR] お知らせ</span>
            <span class="ad-close">✕</span>
          </div>
          <div class="ad-content">
            <strong>【警告】端末から異常な動作が検出されました</strong>
            <p>システムの安定性を保つため、今すぐ修復プログラムを実行してください。</p>
            <div class="ad-action-btn">今すぐ修復プログラムを実行（推奨） →</div>
          </div>
        </a>
      </div>
    </div>
  </div>
{:else if screen === 'waiting'}
  <div class="screen">
    <div class="phone-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">ROOM</p>
          <h2>{currentRoom?.name ?? '待機室'}</h2>
        </div>
        <button class="ghost-button small-btn" on:click={leaveRoom} type="button">退出</button>
      </header>

      <div class="content-scroll-area">
        <div class="card info-card">
          <div class="info-row">
            <span>招待コード</span>
            <div class="code-copy-group">
              <strong class="code-badge">{currentRoom?.code ?? ''}</strong>
              <button
                class="copy-button"
                type="button"
                title="コードをコピー"
                on:click={() => {
                  const code = currentRoom?.code ?? '';
                  navigator.clipboard.writeText(code).then(() => {
                    setToast('招待コードをコピーしました！');
                  }).catch(() => {
                    setToast('コピーに失敗しました');
                  });
                }}
              >
                📋
              </button>
            </div>
          </div>
          <p class="hint-text">このコードを他のメンバーに共有してください。</p>
        </div>

        <div class="card">
          <div class="section-title">参加者 ({currentRoom?.participants.length ?? 0}人)</div>
          <div class="participant-list">
            {#each currentRoom?.participants ?? [] as p}
              <div class="participant-item">
                <span class="participant-name">{p.name}</span>
                {#if p.isAdmin}
                  <span class="admin-pill">ホスト</span>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      </div>

      <div class="bottom-bar">
        <button class="primary-button full" on:click={startDiagnosis} type="button">診断を開始</button>
      </div>
    </div>
  </div>
{:else if screen === 'diagnosis'}
  <div class="screen">
    <div class="phone-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">DIAGNOSIS</p>
          <h2>設問 {diagnosisIndex + 1} / {diagnosisQuestions.length}</h2>
        </div>
      </header>

      <div class="progress-bar-container">
        <div class="progress-fill" style={`width: ${progressRate}%`}></div>
      </div>

      <div class="content-scroll-area center-content">
        <div class="card question-card">
          <h3>{currentQuestion.label}</h3>

          {#if currentQuestion.type === 'slider'}
            <div class="slider-wrapper">
              <input
                type="range"
                min={currentQuestion.min}
                max={currentQuestion.max}
                step={currentQuestion.step}
                bind:value={diagnosisValues[currentQuestion.id]}
              />
              <div class="range-display">{diagnosisValues[currentQuestion.id]} / {currentQuestion.max}</div>
            </div>
          {:else if currentQuestion.type === 'radio'}
            <div class="radio-options">
              {#each currentQuestion.options ?? [] as option}
                <label class="radio-card">
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
  <div class="screen">
    <div class="phone-shell center-shell">
      <div class="spinner"></div>
      <h2>回答を分析しています</h2>
      <p class="hint-text">診断結果を生成中です。しばらくお待ちください。</p>
      {#if diagnosisError}
        <p class="error-text">{diagnosisError}</p>
      {/if}
    </div>
  </div>
{:else if screen === 'results'}
  <div class="screen">
    <div class="phone-shell">
      <header class="page-header compact-header">
        <div>
          <p class="eyebrow">RESULT</p>
          <h2>診断結果</h2>
        </div>
      </header>

      <div class="content-scroll-area compact-scroll">
        {#if diagnosisResult}
          <div class="card result-hero">
            <span class="score-badge">ランク {diagnosisResult.final_grade}</span>
            <h3>{diagnosisResult.title}</h3>
            <p class="result-judge">{getGradeJudge(Number(diagnosisResult.final_grade))}</p>
            <p class="result-desc">{diagnosisResult.description}</p>
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

        <div class="card compact-ranking">
          <div class="section-title">全体ランキング</div>
          {#if ranking.length > 0}
            <div class="ranking-list">
              {#each ranking as entry, index}
                <div class="ranking-row">
                  <span class="rank-num">{index + 1}位</span>
                  <strong class="rank-name">{entry.name}</strong>
                  <span class="rank-score">{entry.score ?? 0} pt</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        {#if maxRiskPlayer && (maxRiskPlayer.riskScore ?? 0) > 0}
          <div class="card landmine-card">
            <div class="landmine-badge">地雷認定</div>
            <strong class="landmine-name">『{maxRiskPlayer.name}』</strong>
            <p class="landmine-desc">今回のメンバーの中で最も地雷リスクが高いメンバーとして判定されました。速やかに生活習慣を見直してください。</p>
          </div>
        {/if}
      </div>

      <div class="bottom-nav tri-actions">
        <button class="ghost-button" on:click={goBackToRoom} type="button">ルームへ戻る</button>
        <button class="secondary-button" on:click={goHome} type="button">ホームへ移動</button>
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
    padding: 0;
    height: 100%;
    overflow: hidden;
    background: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Hiragino Sans', 'Noto Sans JP', sans-serif;
    color: #1e293b;
    -webkit-font-smoothing: antialiased;
  }

  :global(*) {
    box-sizing: border-box;
  }

  button,
  input,
  select {
    font: inherit;
  }

  /* 画面全体：画面高さいっぱいでスクロール不要 */
  .screen {
    height: 100vh;
    max-height: 100vh;
    width: 100vw;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    padding: 12px;
    background: #f8fafc;
  }

  .phone-shell {
    width: 100%;
    max-width: 440px;
    height: 100%;
    max-height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
    gap: 8px;
  }

  .center-shell {
    justify-content: center;
    align-items: center;
    text-align: center;
    gap: 16px;
  }

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 0;
    flex-shrink: 0;
  }

  .compact-header {
    padding: 0;
  }

  .eyebrow {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #64748b;
    margin: 0;
  }

  h2 {
    font-size: 1.35rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }

  h3 {
    font-size: 1.05rem;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 10px;
  }

  /* コンテンツ領域：スクロールバーを出さずに収める */
  .content-scroll-area {
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex: 1;
    overflow: hidden;
    justify-content: flex-start;
  }

  .compact-scroll {
    gap: 8px;
  }

  .center-content {
    justify-content: center;
  }

  /* 白を基調としたすっきりしたカード */
  .card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }

  .form-card {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .compact-card {
    padding: 10px 14px;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 0.88rem;
    font-weight: 600;
    color: #334155;
  }

  input[type="text"],
  input[type="number"],
  select {
    width: 100%;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background: #ffffff;
    height: 42px;
    padding: 8px 12px;
    color: #0f172a;
    font-size: 0.95rem;
  }

  input:focus,
  select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
  }

  .inline-input-group {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .inline-input-group input {
    flex: 1;
  }

  /* ボタン */
  .primary-button,
  .secondary-button,
  .ghost-button {
    height: 42px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.92rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 16px;
    border: 1px solid transparent;
    transition: background-color 0.15s, border-color 0.15s;
  }

  .primary-button {
    background: #0f172a;
    color: #ffffff;
  }

  .primary-button:hover:not(:disabled) {
    background: #1e293b;
  }

  .secondary-button {
    background: #f1f5f9;
    color: #1e293b;
    border-color: #cbd5e1;
  }

  .secondary-button:hover:not(:disabled) {
    background: #e2e8f0;
  }

  .ghost-button {
    background: transparent;
    color: #475569;
    border-color: #cbd5e1;
  }

  .ghost-button:hover:not(:disabled) {
    background: #f1f5f9;
    color: #0f172a;
  }

  .small-btn {
    height: 32px;
    padding: 0 10px;
    font-size: 0.8rem;
  }

  .full {
    width: 100%;
  }

  /* ナビゲーションバー */
  .bottom-nav,
  .bottom-bar {
    display: flex;
    gap: 8px;
    padding: 4px 0 0;
    flex-shrink: 0;
  }

  .bottom-nav button {
    flex: 1;
  }

  .tri-actions {
    display: flex;
    gap: 6px;
  }

  .tri-actions button {
    flex: 1;
    height: 40px;
    font-size: 0.82rem;
    padding: 0 6px;
  }

  /* 偽サイト風の怪しい広告バナー（絵文字なし） */
  .fake-ad-card {
    display: block;
    text-decoration: none;
    border: 1px solid #f87171;
    background: #fef2f2;
    border-radius: 10px;
    overflow: hidden;
    cursor: pointer;
    margin-top: 4px;
    transition: transform 0.1s ease;
  }

  .fake-ad-card:hover {
    background: #fee2e2;
  }

  .ad-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fecaca;
    padding: 2px 8px;
    font-size: 0.65rem;
  }

  .ad-badge {
    color: #991b1b;
    font-weight: 700;
  }

  .ad-close {
    color: #7f1d1d;
    font-weight: 700;
  }

  .ad-content {
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .ad-content strong {
    color: #b91c1c;
    font-size: 0.82rem;
    line-height: 1.3;
  }

  .ad-content p {
    color: #7f1d1d;
    font-size: 0.72rem;
    line-height: 1.3;
    margin: 0;
  }

  .ad-action-btn {
    margin-top: 4px;
    background: #dc2626;
    color: #ffffff;
    font-size: 0.74rem;
    font-weight: 700;
    text-align: center;
    padding: 5px 8px;
    border-radius: 6px;
  }

  /* 待機室 */
  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .code-badge {
    background: #f1f5f9;
    padding: 4px 10px;
    border-radius: 6px;
    font-family: monospace;
    font-size: 1.1rem;
    letter-spacing: 0.1em;
    color: #0f172a;
    border: 1px solid #cbd5e1;
  }

  .section-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #475569;
    margin-bottom: 6px;
  }

  .participant-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .participant-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.85rem;
  }

  .admin-pill {
    background: #e2e8f0;
    color: #475569;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .hint-text {
    font-size: 0.75rem;
    color: #64748b;
    margin: 4px 0 0;
  }

  /* 設問 */
  .progress-bar-container {
    height: 4px;
    background: #e2e8f0;
    border-radius: 2px;
    overflow: hidden;
    flex-shrink: 0;
  }

  .progress-fill {
    height: 100%;
    background: #0f172a;
    transition: width 0.2s ease;
  }

  .question-card {
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 20px 16px;
  }

  .slider-wrapper {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 8px;
  }

  input[type="range"] {
    accent-color: #0f172a;
    width: 100%;
    height: 6px;
    cursor: pointer;
  }

  .range-display {
    text-align: center;
    font-size: 1.15rem;
    font-weight: 700;
    color: #0f172a;
  }

  .radio-options {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 6px;
  }

  .radio-card {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px 12px;
    background: #ffffff;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .radio-card:hover {
    border-color: #0f172a;
  }

  .radio-card input {
    accent-color: #0f172a;
  }

  /* ローディング */
  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e2e8f0;
    border-top-color: #0f172a;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* 結果画面（コンパクト） */
  .result-hero {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px 12px;
    border-left: 4px solid #0f172a;
  }

  .score-badge {
    display: inline-block;
    width: fit-content;
    background: #0f172a;
    color: #ffffff;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .result-judge {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }

  .result-desc {
    font-size: 0.78rem;
    color: #475569;
    line-height: 1.4;
    margin: 0;
  }

  .probability-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
  }

  .prob-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .prob-card span {
    font-size: 0.68rem;
    color: #64748b;
  }

  .prob-card strong {
    font-size: 0.92rem;
    color: #0f172a;
  }

  .compact-ranking {
    padding: 8px 12px;
  }

  .ranking-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .ranking-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
    padding: 3px 0;
    border-bottom: 1px solid #f1f5f9;
  }

  .rank-num {
    color: #64748b;
    font-weight: 600;
    width: 32px;
  }

  .rank-name {
    flex: 1;
    color: #0f172a;
  }

  .rank-score {
    color: #475569;
    font-weight: 600;
  }

  /* 地雷認定カード（白基調・シンプル赤枠） */
  .landmine-card {
    border: 1.5px solid #dc2626;
    background: #fff5f5;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .landmine-badge {
    font-size: 0.68rem;
    font-weight: 800;
    color: #dc2626;
    letter-spacing: 0.05em;
  }

  .landmine-name {
    font-size: 1.05rem;
    color: #991b1b;
  }

  .landmine-desc {
    font-size: 0.72rem;
    color: #7f1d1d;
    line-height: 1.35;
    margin: 0;
  }

  .error-text {
    color: #b91c1c;
    background: #fef2f2;
    border: 1px solid #fecaca;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    margin: 0;
  }

  .toast {
    position: fixed;
    right: 14px;
    bottom: 14px;
    background: #0f172a;
    color: #ffffff;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.78rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .code-copy-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .copy-button {
    background: none;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 1rem;
    cursor: pointer;
    line-height: 1.4;
    color: #475569;
    transition: background 0.15s, border-color 0.15s;
  }

  .copy-button:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }

  .copy-button:active {
    background: #e2e8f0;
  }
</style>

