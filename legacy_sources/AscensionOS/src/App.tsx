import React, { useState, useEffect, useRef } from 'react';
import { 
  Terminal as TerminalIcon, 
  ChefHat, 
  Cpu, 
  Layers, 
  Settings, 
  Folder, 
  Play, 
  RefreshCw, 
  Activity, 
  Send, 
  Check, 
  Sparkles, 
  Dna, 
  Flame, 
  Shield, 
  Sword, 
  Clock, 
  User, 
  Maximize2, 
  Minimize2, 
  X, 
  Search, 
  HelpCircle, 
  AlertCircle,
  FileCode,
  Moon,
  Volume2,
  VolumeX,
  Plus,
  Image,
  Video,
  Music,
  Mic,
  MapPin
} from 'lucide-react';

// Interfaces for our Soul Fusion game
interface BaseHero {
  id: string;
  name: string;
  role: string;
  element: string;
  hp: number;
  atk: number;
  def: number;
  description: string;
  skill: string;
  avatar: string;
}

interface SoulCore {
  id: string;
  name: string;
  element: string;
  hpBonus: number;
  atkBonus: number;
  defBonus: number;
  bonusSkill: string;
  glowColor: string;
  description: string;
}

interface FusedHero {
  name: string;
  baseName: string;
  coreName: string;
  element: string;
  hp: number;
  atk: number;
  def: number;
  primarySkill: string;
  fusedSkill: string;
  avatar: string;
  glow: string;
  rating: string;
}

// Data definitions
const BASE_HEROES: BaseHero[] = [
  {
    id: 'hero-vanguard',
    name: 'Aether Vanguard',
    role: 'Guardian / Defender',
    element: 'Iron / Light',
    hp: 680,
    atk: 48,
    def: 82,
    description: 'A heavily armored sentinel who manipulates celestial iron to shield allies and absorb heavy impact.',
    skill: 'Celestial Bastion (Creates a barrier absorbing 150 damage)',
    avatar: '🛡️'
  },
  {
    id: 'hero-arcanist',
    name: 'Chrono Arcanist',
    role: 'Temporal Mage',
    element: 'Aether / Time',
    hp: 360,
    atk: 92,
    def: 32,
    description: 'A master of temporal flows, bending timelines to release concentrated magical energy.',
    skill: 'Time Warp (Deals 140 magic damage and speeds up attack rate by 50%)',
    avatar: '🔮'
  },
  {
    id: 'hero-assassin',
    name: 'Zephyr Assassin',
    role: 'Swift Striker',
    element: 'Wind / Shadow',
    hp: 420,
    atk: 84,
    def: 40,
    description: 'An agile phantom moving faster than sound, slicing through armor with twin storm daggers.',
    skill: 'Cyclone Slash (Deals 3x critical damage and applies poison)',
    avatar: '🗡️'
  },
  {
    id: 'hero-cleric',
    name: 'Solar Cleric',
    role: 'Support / Healer',
    element: 'Fire / Holy',
    hp: 490,
    atk: 56,
    def: 58,
    description: 'A devotion-driven medic utilizing thermonuclear light to purge toxicity and restore vigor.',
    skill: 'Supernova Rejuvenation (Restores 200 HP and burns adjacent foes)',
    avatar: '☀️'
  }
];

const SOUL_CORES: SoulCore[] = [
  {
    id: 'core-glacial',
    name: 'Glacial Behemoth Core',
    element: 'Ice / Frost',
    hpBonus: 220,
    atkBonus: 10,
    defBonus: 45,
    bonusSkill: 'Sub-Zero Aura (Passively slows down enemy attack velocity and grants cold shield)',
    glowColor: 'cyan',
    description: 'Harvested from deep beneath shifting ice sheets. Instills absolute temperature containment.'
  },
  {
    id: 'core-phoenix',
    name: 'Infernal Phoenix Core',
    element: 'Solar / Flame',
    hpBonus: 80,
    atkBonus: 48,
    defBonus: 12,
    bonusSkill: 'Rebirth Flare (Deals explosive retaliatory fire damage and revives once at 10% HP)',
    glowColor: 'amber',
    description: 'Forged in the heart of dying stars. Ignites the host soul with recursive thermal cycles.'
  },
  {
    id: 'core-stalker',
    name: 'Void Stalker Core',
    element: 'Shadow / Cosmic',
    hpBonus: 110,
    atkBonus: 42,
    defBonus: 18,
    bonusSkill: 'Spectral Phasing (Grants 35% evasion and causes attacks to ignore enemy defensive armor)',
    glowColor: 'rose',
    description: 'Extracted from the outer rims of dark matter singularities. Allows physical phasing.'
  },
  {
    id: 'core-seraph',
    name: 'Cosmic Seraph Core',
    element: 'Divine / Plasma',
    hpBonus: 160,
    atkBonus: 24,
    defBonus: 30,
    bonusSkill: 'Astraea Judgment (Attacks strike with holy plasma arcs, healing the hero for 15% damage dealt)',
    glowColor: 'purple',
    description: 'A pure crystalline matrix humming with celestial equations and high-frequency light.'
  }
];

const SAMPLE_FILES = [
  { name: 'App.tsx', path: '/src/App.tsx', size: '12.4 KB', type: 'TypeScript React' },
  { name: 'server.ts', path: '/server.ts', size: '4.8 KB', type: 'TypeScript Node' },
  { name: 'package.json', path: '/package.json', size: '0.9 KB', type: 'JSON Config' },
  { name: 'index.html', path: '/index.html', size: '0.4 KB', type: 'HTML Document' },
  { name: 'metadata.json', path: '/metadata.json', size: '0.2 KB', type: 'JSON Metadata' },
];

export default function App() {
  // OS Navigation & Settings
  const [activeTab, setActiveTab] = useState<'battler' | 'recipe' | 'ai' | 'labs' | 'files' | 'about'>('battler');
  const [accentColor, setAccentColor] = useState<'cyan' | 'emerald' | 'amber' | 'rose' | 'purple'>('cyan');
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    'Initializing Fusion Hero OS v4.1.0...',
    'System core validation: [OK]',
    'Neural network adapters: Online [High Thinking Enabled]',
    'Welcome back, Operator.',
  ]);
  const [currentTime, setCurrentTime] = useState<string>('');
  const [systemCpu, setSystemCpu] = useState<number>(34);
  const [systemRam, setSystemRam] = useState<number>(5.2);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Soul Fusion Game States
  const [selectedHero, setSelectedHero] = useState<BaseHero | null>(null);
  const [selectedCore, setSelectedCore] = useState<SoulCore | null>(null);
  const [isFusing, setIsFusing] = useState<boolean>(false);
  const [fusedHero, setFusedHero] = useState<FusedHero | null>(null);
  
  // Auto-Battler Simulation States
  const [battleLogs, setBattleLogs] = useState<string[]>([]);
  const [isBattling, setIsBattling] = useState<boolean>(false);
  const [enemyHp, setEnemyHp] = useState<number>(100);
  const [enemyMaxHp, setEnemyMaxHp] = useState<number>(100);
  const [heroHp, setHeroHp] = useState<number>(100);
  const [heroMaxHp, setHeroMaxHp] = useState<number>(100);
  const [battleResult, setBattleResult] = useState<'win' | 'loss' | null>(null);
  const [currentOpponent, setCurrentOpponent] = useState<string>('Abyssal Corruptor');

  // Recipe Fusion States (FusionIsta)
  const [cuisineA, setCuisineA] = useState<string>('Japanese');
  const [cuisineB, setCuisineB] = useState<string>('Mexican');
  const [customIngredient, setCustomIngredient] = useState<string>('');
  const [fusionType, setFusionType] = useState<string>('Molecular Gastronomy');
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);
  const [synthesisLogs, setSynthesisLogs] = useState<string>('');
  const [generatedRecipe, setGeneratedRecipe] = useState<any | null>(null);
  const [recipeError, setRecipeError] = useState<string | null>(null);

  // Intelligence Core Chat States
  const [aiInput, setAiInput] = useState<string>('');
  const [aiMessages, setAiMessages] = useState<Array<{ sender: 'user' | 'ai'; text: string }>>([
    { sender: 'ai', text: 'Greetings, Operator. I am the High-Thinking AI Oracle. Type any logic riddle, architectural design challenge, or complex coding question, and I will unleash deep reasoning to provide an optimal solution.' }
  ]);
  const [isAiThinking, setIsAiThinking] = useState<boolean>(false);
  const [aiError, setAiError] = useState<string | null>(null);

  // 🧪 Neural Labs (Multimedia, Grounding, Image, Video, Music & Voice Conversations) States
  const [labsSubTab, setLabsSubTab] = useState<'chat' | 'media' | 'audio'>('chat');
  
  // Labs Chat & Groundings States
  const [labsChatInput, setLabsChatInput] = useState<string>('');
  const [labsChatMode, setLabsChatMode] = useState<'high-thinking' | 'low-latency' | 'search-grounding' | 'maps-grounding'>('search-grounding');
  const [labsChatMessages, setLabsChatMessages] = useState<Array<{ sender: 'user' | 'ai'; text: string; mode?: string; groundingChunks?: any[] }>>([
    { 
      sender: 'ai', 
      text: 'Neural Labs Core Active. Choose a Grounding, low-latency, or thinking profile and submit your query.',
      mode: 'search-grounding'
    }
  ]);
  const [isLabsChatLoading, setIsLabsChatLoading] = useState<boolean>(false);
  const [labsChatError, setLabsChatError] = useState<string | null>(null);
  
  // Labs Media (Image & Video Gen, Media Analysis) States
  const [imagePrompt, setImagePrompt] = useState<string>('A stunning neon cyberpunk matrix terminal in 8k resolution');
  const [imageAspectRatio, setImageAspectRatio] = useState<string>('16:9');
  const [imageSize, setImageSize] = useState<string>('1K');
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string>('');
  const [isGeneratingImage, setIsGeneratingImage] = useState<boolean>(false);
  const [imageError, setImageError] = useState<string | null>(null);
  
  const [uploadedMedia, setUploadedMedia] = useState<string>('');
  const [uploadedMediaMime, setUploadedMediaMime] = useState<string>('');
  const [mediaAnalysisPrompt, setMediaAnalysisPrompt] = useState<string>('Examine this telemetry report or screenshot and list key structural anomalies.');
  const [mediaAnalysisResult, setMediaAnalysisResult] = useState<string>('');
  const [isAnalyzingMedia, setIsAnalyzingMedia] = useState<boolean>(false);
  const [mediaAnalysisError, setMediaAnalysisError] = useState<string | null>(null);
  
  const [videoPrompt, setVideoPrompt] = useState<string>('Cybernetic neural stream of glowing numbers cascading like digital rain');
  const [videoAspectRatio, setVideoAspectRatio] = useState<string>('16:9');
  const [videoResolution, setVideoResolution] = useState<string>('720p');
  const [videoGenerationStatus, setVideoGenerationStatus] = useState<'idle' | 'generating' | 'polling' | 'completed' | 'error'>('idle');
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string>('');
  const [videoLogs, setVideoLogs] = useState<string>('');
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoOperationName, setVideoOperationName] = useState<string>('');
  
  // Labs Audio (TTS Voice, Audio Transcription, Lyria Music) States
  const [transcriptionText, setTranscriptionText] = useState<string>('');
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);
  const [transcriptionError, setTranscriptionError] = useState<string | null>(null);
  
  const [ttsInputText, setTtsInputText] = useState<string>('Accessing satellite link. Core modules successfully initialized.');
  const [ttsVoice, setTtsVoice] = useState<string>('Zephyr');
  const [generatedTtsUrl, setGeneratedTtsUrl] = useState<string>('');
  const [isTtsLoading, setIsTtsLoading] = useState<boolean>(false);
  const [ttsError, setTtsError] = useState<string | null>(null);
  
  const [musicPrompt, setMusicPrompt] = useState<string>('Upbeat retro 16-bit chiptune sound with neon cyber aesthetic');
  const [musicLength, setMusicLength] = useState<string>('short');
  const [generatedMusicUrl, setGeneratedMusicUrl] = useState<string>('');
  const [generatedMusicLyrics, setGeneratedMusicLyrics] = useState<string>('');
  const [isGeneratingMusic, setIsGeneratingMusic] = useState<boolean>(false);
  const [musicError, setMusicError] = useState<string | null>(null);

  // Mock File System Viewer State
  const [selectedFile, setSelectedFile] = useState<string>('App.tsx');
  const [workspaceFiles, setWorkspaceFiles] = useState<Array<{ name: string; path: string; size: string; content: string }>>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(false);

  // Fetch actual workspace files on mount
  useEffect(() => {
    const fetchFiles = async () => {
      setIsLoadingFiles(true);
      try {
        const response = await fetch('/api/workspace/files');
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data) && data.length > 0) {
            setWorkspaceFiles(data);
          }
        }
      } catch (error) {
        console.error('Failed to load workspace files:', error);
      } finally {
        setIsLoadingFiles(false);
      }
    };
    fetchFiles();
  }, []);

  // Real-time Clock and simulated CPU fluctuations
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false }));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);

    const metricsTimer = setInterval(() => {
      setSystemCpu(prev => {
        const delta = Math.floor(Math.random() * 15) - 7;
        const next = prev + delta;
        return Math.max(15, Math.min(next, 95));
      });
      setSystemRam(prev => {
        const delta = Number((Math.random() * 0.4 - 0.2).toFixed(1));
        const next = Number((prev + delta).toFixed(1));
        return Math.max(4.5, Math.min(next, 7.8));
      });
    }, 4000);

    return () => {
      clearInterval(timer);
      clearInterval(metricsTimer);
    };
  }, []);

  // Scroll terminal logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLogs]);

  // Play audio effect
  const playSound = (type: 'click' | 'fuse' | 'battle' | 'error' | 'success') => {
    if (!soundEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);

      if (type === 'click') {
        osc.frequency.setValueAtTime(600, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.1);
      } else if (type === 'fuse') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(150, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(800, audioCtx.currentTime + 0.8);
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.8);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.8);
      } else if (type === 'battle') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(220, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(110, audioCtx.currentTime + 0.2);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.25);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.25);
      } else if (type === 'success') {
        osc.frequency.setValueAtTime(440, audioCtx.currentTime);
        osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.15);
        gain.gain.setValueAtTime(0.07, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
      } else if (type === 'error') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(130, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.5);
      }
    } catch (e) {
      // Ignored if browser blocks AudioContext on startup
    }
  };

  const addLog = (message: string) => {
    setTerminalLogs(prev => [...prev, `[${new Date().toLocaleTimeString('en-US', { hour12: false })}] ${message}`]);
  };

  // Accent Colors Mapper
  const accentClasses = {
    cyan: {
      text: 'text-cyan-400',
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/30',
      borderGlow: 'shadow-[0_0_15px_rgba(34,211,238,0.25)]',
      bgSolid: 'bg-cyan-500',
      accentGlow: 'rgba(34,211,238,0.4)',
      textHover: 'hover:text-cyan-300',
      bgHover: 'hover:bg-cyan-500/20'
    },
    emerald: {
      text: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      borderGlow: 'shadow-[0_0_15px_rgba(16,185,129,0.25)]',
      bgSolid: 'bg-emerald-500',
      accentGlow: 'rgba(16,185,129,0.4)',
      textHover: 'hover:text-emerald-300',
      bgHover: 'hover:bg-emerald-500/20'
    },
    amber: {
      text: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
      borderGlow: 'shadow-[0_0_15px_rgba(245,158,11,0.25)]',
      bgSolid: 'bg-amber-500',
      accentGlow: 'rgba(245,158,11,0.4)',
      textHover: 'hover:text-amber-300',
      bgHover: 'hover:bg-amber-500/20'
    },
    rose: {
      text: 'text-rose-400',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/30',
      borderGlow: 'shadow-[0_0_15px_rgba(244,63,94,0.25)]',
      bgSolid: 'bg-rose-500',
      accentGlow: 'rgba(244,63,94,0.4)',
      textHover: 'hover:text-rose-300',
      bgHover: 'hover:bg-rose-500/20'
    },
    purple: {
      text: 'text-purple-400',
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/30',
      borderGlow: 'shadow-[0_0_15px_rgba(168,85,247,0.25)]',
      bgSolid: 'bg-purple-500',
      accentGlow: 'rgba(168,85,247,0.4)',
      textHover: 'hover:text-purple-300',
      bgHover: 'hover:bg-purple-500/20'
    }
  };

  const currentTheme = accentClasses[accentColor];

  // Action: Soul Fusion execution
  const handleExecuteSoulFusion = () => {
    if (!selectedHero || !selectedCore) {
      playSound('error');
      addLog('ERR: Unable to fuse. Missing target matrix coordinates.');
      return;
    }

    playSound('fuse');
    setIsFusing(true);
    addLog(`Initiating soul merger: [${selectedHero.name}] + [${selectedCore.name}]`);
    
    setTimeout(() => {
      // Create spectacular fused hero
      const prefix = selectedCore.name.split(' ')[0]; // e.g. Glacial, Infernal
      const suffix = selectedHero.name.split(' ')[1]; // e.g. Vanguard, Arcanist
      const fusedName = `${prefix} ${suffix}`;
      
      const newFused: FusedHero = {
        name: fusedName,
        baseName: selectedHero.name,
        coreName: selectedCore.name,
        element: `${selectedHero.element} / ${selectedCore.element}`,
        hp: selectedHero.hp + selectedCore.hpBonus,
        atk: selectedHero.atk + selectedCore.atkBonus,
        def: selectedHero.def + selectedCore.defBonus,
        primarySkill: selectedHero.skill,
        fusedSkill: selectedCore.bonusSkill,
        avatar: selectedHero.avatar,
        glow: selectedCore.glowColor,
        rating: ['S', 'SS', 'SSS', 'ULTRA'][Math.floor(Math.random() * 4)]
      };

      setFusedHero(newFused);
      setIsFusing(false);
      playSound('success');
      addLog(`Fusion successful. New lifeform locked: ${fusedName} (Tier ${newFused.rating})`);
      
      // Update battlefield defaults
      setHeroHp(newFused.hp);
      setHeroMaxHp(newFused.hp);
      setEnemyHp(newFused.hp - 100 > 300 ? newFused.hp - 100 : 350);
      setEnemyMaxHp(newFused.hp - 100 > 300 ? newFused.hp - 100 : 350);
      setBattleResult(null);
      setBattleLogs([]);
    }, 2000);
  };

  // Action: Simulated Auto-Battle
  const handleStartBattle = () => {
    if (!fusedHero) return;
    playSound('click');
    setIsBattling(true);
    setBattleResult(null);
    setBattleLogs([`⚔️ Battlefield loaded. [${fusedHero.name}] vs [${currentOpponent}]`]);

    let currHeroHp = heroMaxHp;
    let currEnemyHp = enemyMaxHp;
    setHeroHp(currHeroHp);
    setEnemyHp(currEnemyHp);

    let round = 1;

    const interval = setInterval(() => {
      if (currHeroHp <= 0 || currEnemyHp <= 0) {
        clearInterval(interval);
        setIsBattling(false);
        if (currHeroHp > 0) {
          setBattleResult('win');
          playSound('success');
          addLog(`Simulated victory achieved against ${currentOpponent}!`);
        } else {
          setBattleResult('loss');
          playSound('error');
          addLog(`Simulation failure. Host form destabilized.`);
        }
        return;
      }

      const logLines: string[] = [];
      playSound('battle');

      // Hero attacks
      const heroDamage = Math.floor(Math.random() * 20) + fusedHero.atk - Math.floor(Math.random() * 10);
      const skillTrigger = Math.random() < 0.35;
      
      if (skillTrigger) {
        currEnemyHp -= (heroDamage + 40);
        logLines.push(`✨ Round ${round}: [${fusedHero.name}] triggers [${fusedHero.fusedSkill.split(' (')[0]}]! Strikes for ${heroDamage + 40} plasma damage.`);
      } else {
        currEnemyHp -= heroDamage;
        logLines.push(`⚔️ Round ${round}: [${fusedHero.name}] attacks [${currentOpponent}] for ${heroDamage} damage.`);
      }

      // Check enemy alive
      if (currEnemyHp <= 0) {
        currEnemyHp = 0;
        logLines.push(`🏆 [${currentOpponent}] has been completely vaporized!`);
        setEnemyHp(0);
        setBattleLogs(prev => [...prev, ...logLines]);
        return;
      }

      // Enemy attacks
      const enemyAtk = Math.floor(Math.random() * 25) + 35;
      const enemyDamage = Math.max(10, enemyAtk - Math.floor(fusedHero.def / 5));
      currHeroHp -= enemyDamage;
      logLines.push(`💀 Round ${round}: [${currentOpponent}] retaliates with Dark Claw dealing ${enemyDamage} damage to [${fusedHero.name}].`);

      if (currHeroHp <= 0) {
        currHeroHp = 0;
        logLines.push(`🛑 [${fusedHero.name}] structural integrity critical! Disconnecting core.`);
      }

      setHeroHp(currHeroHp);
      setEnemyHp(currEnemyHp);
      setBattleLogs(prev => [...prev, ...logLines]);
      round++;
    }, 1200);
  };

  // Action: FusionIsta Recipe Molecular Synthesis
  const handleSynthesizeRecipe = async () => {
    playSound('click');
    setIsSynthesizing(true);
    setRecipeError(null);
    setGeneratedRecipe(null);
    setSynthesisLogs('Calibrating molecular flavor vectors...');

    const logStates = [
      'Calibrating molecular flavor vectors...',
      'Analyzing chemical spice compatibility curves...',
      'Modeling cellular restructuring techniques...',
      'Calling Gemini reasoning chain (free-tier flash first, Pro if available)...',
      'Refining gourmet geometric plating algorithms...'
    ];

    let logIdx = 0;
    const logInterval = setInterval(() => {
      if (logIdx < logStates.length - 1) {
        logIdx++;
        setSynthesisLogs(logStates[logIdx]);
      }
    }, 1500);

    try {
      const targetCuisineA = cuisineA;
      const targetCuisineB = cuisineB;
      const itemA = customIngredient ? `${targetCuisineA} (${customIngredient})` : targetCuisineA;
      const itemB = targetCuisineB;

      const response = await fetch('/api/gemini/recipe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ itemA, itemB, fusionType })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Server Synthesis Interrupted');
      }

      const recipe = await response.json();
      setGeneratedRecipe(recipe);
      addLog(`Recipe synthesized successfully: "${recipe.name}"`);
      playSound('success');
    } catch (err: any) {
      console.error(err);
      setRecipeError(err.message || 'Error occurred during high thinking molecular synthesis.');
      addLog(`ERR: Molecular synthesis failed. Core temperature spike detected.`);
      playSound('error');
    } finally {
      clearInterval(logInterval);
      setIsSynthesizing(false);
    }
  };

  // Action: High-Thinking AI Query
  const handleSendAiMessage = async () => {
    if (!aiInput.trim()) return;
    
    const userMsg = aiInput;
    setAiInput('');
    setAiMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setIsAiThinking(true);
    setAiError(null);
    addLog(`AI Query sent to Neural Core: "${userMsg.slice(0, 30)}..."`);
    playSound('click');

    try {
      const response = await fetch('/api/gemini/thinking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'High Thinking Core interrupted.');
      }

      const data = await response.json();
      setAiMessages(prev => [...prev, { sender: 'ai', text: data.text }]);
      addLog(`Intelligence Core successfully processed complex logic statement.`);
      playSound('success');
    } catch (err: any) {
      console.error(err);
      setAiError(err.message || 'Failed to process logical reasoning model.');
      playSound('error');
    } finally {
      setIsAiThinking(false);
    }
  };

  // 🧪 Neural Labs Chat & Groundings Action
  const handleSendLabsChatMessage = async () => {
    if (!labsChatInput.trim() || isLabsChatLoading) return;
    
    const userMsg = labsChatInput;
    setLabsChatInput('');
    setLabsChatMessages(prev => [...prev, { sender: 'user', text: userMsg, mode: labsChatMode }]);
    setIsLabsChatLoading(true);
    setLabsChatError(null);
    addLog(`Labs query sent [mode: ${labsChatMode}]: "${userMsg.slice(0, 30)}..."`);
    playSound('click');

    // Get current browser coordinates for Maps Grounding if available
    let latitude = 37.7749;
    let longitude = -122.4194;
    
    const sendRequest = async (lat?: number, lon?: number) => {
      try {
        const response = await fetch('/api/gemini/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            message: userMsg, 
            mode: labsChatMode,
            latitude: lat || latitude,
            longitude: lon || longitude
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Labs node communication failure.');
        }

        const data = await response.json();
        setLabsChatMessages(prev => [...prev, { 
          sender: 'ai', 
          text: data.text, 
          mode: labsChatMode, 
          groundingChunks: data.groundingChunks 
        }]);
        addLog(`Labs intelligence core processed grounded query successfully.`);
        playSound('success');
      } catch (err: any) {
        console.error(err);
        setLabsChatError(err.message || 'Error occurred during grounding query.');
        playSound('error');
      } finally {
        setIsLabsChatLoading(false);
      }
    };

    if (labsChatMode === 'maps-grounding' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => sendRequest(pos.coords.latitude, pos.coords.longitude),
        () => sendRequest() // fallback to standard coords on permission deny
      );
    } else {
      sendRequest();
    }
  };

  // 🧪 Neural Labs Image Generation Action
  const handleGenerateImage = async () => {
    if (isGeneratingImage) return;
    
    setIsGeneratingImage(true);
    setImageError(null);
    setGeneratedImageUrl('');
    addLog(`Initiated high-fidelity Image Gen matrix: [${imageSize} @ ${imageAspectRatio}]`);
    playSound('click');

    try {
      const response = await fetch('/api/gemini/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: imagePrompt, 
          aspectRatio: imageAspectRatio, 
          imageSize: imageSize 
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Image generation server error.');
      }

      const data = await response.json();
      setGeneratedImageUrl(data.imageUrl);
      addLog(`Image Gen matrix completed successfully.`);
      playSound('success');
    } catch (err: any) {
      console.error(err);
      setImageError(err.message || 'Image generation failed.');
      playSound('error');
    } finally {
      setIsGeneratingImage(false);
    }
  };

  // 🧪 Neural Labs Media Analysis Action
  const handleAnalyzeMedia = async () => {
    if (!uploadedMedia || isAnalyzingMedia) return;
    
    setIsAnalyzingMedia(true);
    setMediaAnalysisError(null);
    setMediaAnalysisResult('');
    addLog(`Analyzing file matrix stream...`);
    playSound('click');

    try {
      const response = await fetch('/api/gemini/analyze-media', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          fileBase64: uploadedMedia.split(',')[1] || uploadedMedia, 
          mimeType: uploadedMediaMime, 
          prompt: mediaAnalysisPrompt 
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Media analyzer node failure.');
      }

      const data = await response.json();
      setMediaAnalysisResult(data.text);
      addLog(`Media analysis completed. Report loaded to terminal.`);
      playSound('success');
    } catch (err: any) {
      console.error(err);
      setMediaAnalysisError(err.message || 'Media analysis failed.');
      playSound('error');
    } finally {
      setIsAnalyzingMedia(false);
    }
  };

  // Helper to handle image upload selection
  const handleMediaUploadChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedMediaMime(file.type);
    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        setUploadedMedia(event.target.result as string);
        addLog(`File successfully read: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);
        playSound('success');
      }
    };
    reader.readAsDataURL(file);
  };

  // 🧪 Neural Labs Audio Transcription Action
  const handleTranscribeAudio = async (base64Audio: string, mime: string) => {
    setIsTranscribing(true);
    setTranscriptionError(null);
    setTranscriptionText('');
    addLog(`Transcribing audio packet...`);

    try {
      const response = await fetch('/api/gemini/transcribe-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          fileBase64: base64Audio, 
          mimeType: mime 
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Transcription node failure.');
      }

      const data = await response.json();
      setTranscriptionText(data.text);
      addLog(`Transcription completed successfully.`);
      playSound('success');
    } catch (err: any) {
      console.error(err);
      setTranscriptionError(err.message || 'Transcription failed.');
      playSound('error');
    } finally {
      setIsTranscribing(false);
    }
  };

  // 🧪 Neural Labs Text to Speech Action
  const handleTtsGenerate = async () => {
    if (!ttsInputText.trim() || isTtsLoading) return;
    
    setIsTtsLoading(true);
    setTtsError(null);
    setGeneratedTtsUrl('');
    addLog(`Synthesizing spoken audio stream [voice: ${ttsVoice}]...`);
    playSound('click');

    try {
      const response = await fetch('/api/gemini/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: ttsInputText, 
          voice: ttsVoice 
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'TTS synthesizer failed.');
      }

      const data = await response.json();
      
      // Decode base64 to Blob URL
      const binary = atob(data.audioBase64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'audio/pcm' });
      
      // Convert PCM to standard playable format on-the-fly or feed to AudioContext if raw
      // To ensure maximum browser native compatibility, we wrap standard audio/wav or raw PCM
      // Note: gemini-3.1-flash-tts-preview audio outputs raw PCM rate=24000. Let's make it playable!
      const audioUrl = URL.createObjectURL(blob);
      setGeneratedTtsUrl(audioUrl);
      addLog(`Voice synthesis complete. Audio link ready.`);
      playSound('success');
    } catch (err: any) {
      console.error(err);
      setTtsError(err.message || 'TTS generation failed.');
      playSound('error');
    } finally {
      setIsTtsLoading(false);
    }
  };

  // 🧪 Neural Labs Lyria Music Generation Action
  const handleGenerateMusic = async () => {
    if (isGeneratingMusic) return;
    
    setIsGeneratingMusic(true);
    setMusicError(null);
    setGeneratedMusicUrl('');
    setGeneratedMusicLyrics('');
    addLog(`Contacting Google Lyria Music model [length: ${musicLength}]...`);
    playSound('click');

    try {
      const response = await fetch('/api/gemini/generate-music', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: musicPrompt, 
          length: musicLength 
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Lyria synthesizer offline.');
      }

      const data = await response.json();
      
      const binary = atob(data.audioBase64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: data.mimeType || 'audio/wav' });
      const audioUrl = URL.createObjectURL(blob);
      
      setGeneratedMusicUrl(audioUrl);
      setGeneratedMusicLyrics(data.lyrics || '');
      addLog(`Lyria synthesis complete. Spaced out ambient retro loops populated.`);
      playSound('success');
    } catch (err: any) {
      console.error(err);
      setMusicError(err.message || 'Music generation failed.');
      playSound('error');
    } finally {
      setIsGeneratingMusic(false);
    }
  };

  // 🧪 Neural Labs Veo Video Generation Action (3-Step setup)
  const handleGenerateVideo = async () => {
    if (videoGenerationStatus === 'generating' || videoGenerationStatus === 'polling') return;
    
    setVideoGenerationStatus('generating');
    setVideoError(null);
    setGeneratedVideoUrl('');
    setVideoLogs('Contacting Veo 3.1 video processor...');
    addLog(`Starting Veo 3.1 video reactor...`);
    playSound('click');

    try {
      // Step 1: Start video operation
      const response = await fetch('/api/gemini/generate-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: videoPrompt, 
          aspectRatio: videoAspectRatio, 
          resolution: videoResolution 
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Veo server rejected request.');
      }

      const data = await response.json();
      const opName = data.operationName;
      setVideoOperationName(opName);
      setVideoGenerationStatus('polling');
      setVideoLogs(`Operation started: ${opName.split('/').pop()}`);

      // Step 2 & 3: Poll until complete
      const pollStates = [
        'Instantiating neural wireframes...',
        'Compiling voxel trajectories...',
        'Applying deep lighting shaders...',
        'Encoding progressive video stream...',
        'Polishing resolution textures...'
      ];
      
      let pollCount = 0;
      const pollInterval = setInterval(async () => {
        try {
          // progressive status updates
          if (pollCount < pollStates.length) {
            setVideoLogs(pollStates[pollCount]);
            pollCount++;
          } else {
            setVideoLogs('Compiling final neural codec array...');
          }

          const statusRes = await fetch('/api/gemini/video-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ operationName: opName })
          });

          if (!statusRes.ok) {
            throw new Error('Failed to verify operation status.');
          }

          const statusData = await statusRes.json();
          if (statusData.done) {
            clearInterval(pollInterval);
            setVideoLogs('Finalizing asset download stream...');

            // Step 3: Fetch download
            const downloadRes = await fetch('/api/gemini/video-download', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ operationName: opName })
            });

            if (!downloadRes.ok) {
              throw new Error('Video retrieval stream corrupted.');
            }

            const videoBlob = await downloadRes.blob();
            const videoUrl = URL.createObjectURL(videoBlob);
            setGeneratedVideoUrl(videoUrl);
            setVideoGenerationStatus('completed');
            setVideoLogs('Veo 3.1 video rendered and downloaded successfully.');
            addLog(`Veo video downloaded successfully.`);
            playSound('success');
          }
        } catch (pollErr: any) {
          console.error(pollErr);
          clearInterval(pollInterval);
          setVideoGenerationStatus('error');
          setVideoError(pollErr.message || 'Polling error occurred.');
          playSound('error');
        }
      }, 7000); // Poll every 7 seconds as Veo operation takes a bit

    } catch (err: any) {
      console.error(err);
      setVideoGenerationStatus('error');
      setVideoError(err.message || 'Video generation failed.');
      playSound('error');
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0c10] text-[#cfd4de] font-sans antialiased overflow-x-hidden flex flex-col selection:bg-cyan-500/30 selection:text-white cyber-scanlines">
      
      {/* 🚀 Top Cybernetic Operating System Status Bar */}
      <header className="border-b border-[#1b2230] bg-[#0c0f16] px-4 py-2.5 flex items-center justify-between text-xs tracking-wider font-mono">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${currentTheme.bgSolid} animate-pulse shadow-[0_0_10px_currentColor]`}></span>
            <span className="font-bold text-white tracking-widest">FUSION-HERO // OS</span>
          </div>
          <span className="text-[#5a657a] hidden md:inline">|</span>
          <div className="hidden md:flex items-center gap-1.5 text-[#8892b0]">
            <Activity size={13} className={currentTheme.text} />
            <span>METRIC:</span>
            <span className="text-[#a8b2d1]">CPU {systemCpu}%</span>
            <span className="text-[#5a657a] ml-1">/</span>
            <span className="text-[#a8b2d1]">RAM {systemRam} GB</span>
          </div>
        </div>

        {/* System Settings panel top-right */}
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-1">
            <Clock size={13} className="text-gray-400" />
            <span className="text-gray-200">{currentTime || '00:00:00'}</span>
          </div>

          <div className="flex items-center gap-3 border-l border-[#1b2230] pl-4">
            {/* Audio Toggle */}
            <button 
              onClick={() => { setSoundEnabled(!soundEnabled); playSound('click'); }} 
              className="text-[#8892b0] hover:text-white transition-colors"
              title={soundEnabled ? "Disable Sonic Feedback" : "Enable Sonic Feedback"}
            >
              {soundEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
            </button>

            {/* Accent Changer */}
            <div className="flex gap-1.5 items-center bg-[#131924] p-1 rounded border border-[#1b2230]">
              {(['cyan', 'emerald', 'amber', 'rose', 'purple'] as const).map(color => (
                <button
                  key={color}
                  onClick={() => { setAccentColor(color); playSound('click'); }}
                  className={`w-3.5 h-3.5 rounded-full transition-transform ${
                    color === 'cyan' ? 'bg-cyan-400' :
                    color === 'emerald' ? 'bg-emerald-400' :
                    color === 'amber' ? 'bg-amber-400' :
                    color === 'rose' ? 'bg-rose-400' : 'bg-purple-400'
                  } ${accentColor === color ? 'scale-125 ring-2 ring-white/40' : 'opacity-70 hover:opacity-100'}`}
                />
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* 💻 Primary Workspace Layout (Two-column layout optimized for iframe previews) */}
      <main className="flex-1 flex flex-col lg:flex-row min-h-0 bg-[#080a0f]">
        
        {/* Left Side: Dynamic App Workspace Panel */}
        <section className="flex-1 p-4 lg:p-6 flex flex-col min-h-0 overflow-y-auto">
          
          {/* OS Navigation Tabs */}
          <nav className="flex flex-wrap gap-2 mb-6 border-b border-[#1b2230] pb-3" id="os-navbar">
            <button
              onClick={() => { setActiveTab('battler'); playSound('click'); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs tracking-wider uppercase transition-all border ${
                activeTab === 'battler' 
                  ? `${currentTheme.text} ${currentTheme.bg} ${currentTheme.border} ${currentTheme.borderGlow}` 
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#121824]'
              }`}
            >
              <Layers size={14} />
              Soul Battler
            </button>

            <button
              onClick={() => { setActiveTab('recipe'); playSound('click'); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs tracking-wider uppercase transition-all border ${
                activeTab === 'recipe' 
                  ? `${currentTheme.text} ${currentTheme.bg} ${currentTheme.border} ${currentTheme.borderGlow}` 
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#121824]'
              }`}
            >
              <ChefHat size={14} />
              FusionIsta Lab
            </button>

            <button
              onClick={() => { setActiveTab('ai'); playSound('click'); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs tracking-wider uppercase transition-all border ${
                activeTab === 'ai' 
                  ? `${currentTheme.text} ${currentTheme.bg} ${currentTheme.border} ${currentTheme.borderGlow}` 
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#121824]'
              }`}
            >
              <Cpu size={14} />
              Intelligence Core
            </button>

            <button
              onClick={() => { setActiveTab('labs'); playSound('click'); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs tracking-wider uppercase transition-all border ${
                activeTab === 'labs' 
                  ? `${currentTheme.text} ${currentTheme.bg} ${currentTheme.border} ${currentTheme.borderGlow}` 
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#121824]'
              }`}
            >
              <Sparkles size={14} className="text-pink-400 animate-pulse" />
              Neural Labs Matrix
            </button>

            <button
              onClick={() => { setActiveTab('files'); playSound('click'); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs tracking-wider uppercase transition-all border ${
                activeTab === 'files' 
                  ? `${currentTheme.text} ${currentTheme.bg} ${currentTheme.border} ${currentTheme.borderGlow}` 
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#121824]'
              }`}
            >
              <Folder size={14} />
              Environment Files
            </button>

            <button
              onClick={() => { setActiveTab('about'); playSound('click'); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs tracking-wider uppercase transition-all border ${
                activeTab === 'about' 
                  ? `${currentTheme.text} ${currentTheme.bg} ${currentTheme.border} ${currentTheme.borderGlow}` 
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#121824]'
              }`}
            >
              <HelpCircle size={14} />
              About OS
            </button>
          </nav>

          {/* Active View Port Frame */}
          <div className="flex-1 bg-[#0b0e16] border border-[#1b2230] rounded-xl p-5 md:p-6 shadow-[0_4px_30px_rgba(0,0,0,0.4)] relative flex flex-col justify-between">
            
            {/* 1. App: Soul Battler Auto-Battler */}
            {activeTab === 'battler' && (
              <div className="flex-1 flex flex-col justify-between gap-6">
                <div>
                  <h2 className="font-display text-xl font-bold text-white flex items-center gap-2">
                    <Layers className={currentTheme.text} />
                    Auto-Battler Soul Fusion
                  </h2>
                  <p className="text-gray-400 text-xs mt-1 font-mono">
                    Forge complex warriors by merging baseline entities with cosmological soul cores. Sim battles against waves.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-auto">
                  
                  {/* Step A: Base Hero Select */}
                  <div className="bg-[#121722] border border-[#1f283a] rounded-xl p-4 flex flex-col gap-3">
                    <h3 className="text-xs font-mono tracking-wider text-gray-400 border-b border-[#1f283a] pb-2 uppercase flex items-center justify-between">
                      <span>1. Select Base Vanguard Matrix</span>
                      {selectedHero && <Check size={14} className="text-emerald-400" />}
                    </h3>
                    
                    <div className="grid grid-cols-2 gap-2">
                      {BASE_HEROES.map(hero => (
                        <button
                          key={hero.id}
                          onClick={() => { setSelectedHero(hero); playSound('click'); }}
                          className={`p-2.5 rounded-lg border text-left transition-all flex flex-col gap-1.5 ${
                            selectedHero?.id === hero.id
                              ? `${currentTheme.border} ${currentTheme.bg} text-white`
                              : 'border-[#1f283a] bg-[#0c1018] text-[#8e98ac] hover:bg-[#161d2d] hover:text-white'
                          }`}
                        >
                          <div className="flex items-center gap-1.5 font-bold text-sm">
                            <span>{hero.avatar}</span>
                            <span>{hero.name.split(' ')[1]}</span>
                          </div>
                          <div className="flex gap-2 text-[10px] font-mono">
                            <span className="text-rose-400">HP {hero.hp}</span>
                            <span className="text-amber-400">ATK {hero.atk}</span>
                          </div>
                        </button>
                      ))}
                    </div>

                    {selectedHero && (
                      <div className="bg-[#0b0e16] p-3 rounded-lg border border-[#1b2230] text-xs">
                        <div className="font-bold text-white mb-1">{selectedHero.name}</div>
                        <p className="text-gray-400 text-[11px] leading-relaxed mb-1">{selectedHero.description}</p>
                        <span className="text-cyan-400 font-mono text-[10px]">Matrix Skill: {selectedHero.skill}</span>
                      </div>
                    )}
                  </div>

                  {/* Step B: Soul Core Select */}
                  <div className="bg-[#121722] border border-[#1f283a] rounded-xl p-4 flex flex-col gap-3">
                    <h3 className="text-xs font-mono tracking-wider text-gray-400 border-b border-[#1f283a] pb-2 uppercase flex items-center justify-between">
                      <span>2. Inject Core Energy Modulator</span>
                      {selectedCore && <Check size={14} className="text-emerald-400" />}
                    </h3>

                    <div className="grid grid-cols-2 gap-2">
                      {SOUL_CORES.map(core => (
                        <button
                          key={core.id}
                          onClick={() => { setSelectedCore(core); playSound('click'); }}
                          className={`p-2.5 rounded-lg border text-left transition-all flex flex-col gap-1.5 ${
                            selectedCore?.id === core.id
                              ? `${currentTheme.border} ${currentTheme.bg} text-white`
                              : 'border-[#1f283a] bg-[#0c1018] text-[#8e98ac] hover:bg-[#161d2d] hover:text-white'
                          }`}
                        >
                          <div className="flex items-center gap-1.5 font-bold text-sm">
                            <span className={`w-2.5 h-2.5 rounded-full ${
                              core.glowColor === 'cyan' ? 'bg-cyan-400 shadow-[0_0_8px_#22d3ee]' :
                              core.glowColor === 'amber' ? 'bg-amber-400 shadow-[0_0_8px_#f59e0b]' :
                              core.glowColor === 'rose' ? 'bg-rose-400 shadow-[0_0_8px_#f43f5e]' :
                              'bg-purple-400 shadow-[0_0_8px_#a855f7]'
                            }`}></span>
                            <span>{core.name.split(' ')[0]}</span>
                          </div>
                          <div className="flex gap-2 text-[10px] font-mono">
                            <span className="text-rose-400">+{core.hpBonus}</span>
                            <span className="text-amber-400">+{core.atkBonus}</span>
                          </div>
                        </button>
                      ))}
                    </div>

                    {selectedCore && (
                      <div className="bg-[#0b0e16] p-3 rounded-lg border border-[#1b2230] text-xs">
                        <div className="font-bold text-white mb-1">{selectedCore.name}</div>
                        <p className="text-gray-400 text-[11px] leading-relaxed mb-1">{selectedCore.description}</p>
                        <span className="text-amber-400 font-mono text-[10px]">Soul Passive: {selectedCore.bonusSkill}</span>
                      </div>
                    )}
                  </div>

                </div>

                {/* Fuse Activator Bar */}
                <div className="flex flex-col gap-4 border-t border-[#1b2230] pt-4">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="text-xs text-gray-400">
                      {selectedHero && selectedCore ? (
                        <span className="text-emerald-400 font-mono">✓ READY FOR MOLECULAR QUANTUM FUSION</span>
                      ) : (
                        <span className="text-[#8892b0] font-mono">⚠ Selection incomplete. Please coordinate nodes above.</span>
                      )}
                    </div>

                    <button
                      disabled={!selectedHero || !selectedCore || isFusing}
                      onClick={handleExecuteSoulFusion}
                      className={`px-6 py-2.5 rounded-xl font-mono text-sm font-bold tracking-widest uppercase transition-all duration-300 ${
                        selectedHero && selectedCore && !isFusing
                          ? `${currentTheme.bgSolid} text-black hover:opacity-90 cursor-pointer shadow-[0_0_20px_currentColor]`
                          : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      {isFusing ? (
                        <span className="flex items-center gap-2">
                          <RefreshCw className="animate-spin" size={16} />
                          FUSING QUANTUM STATES...
                        </span>
                      ) : 'EXECUTE SOUL FUSION'}
                    </button>
                  </div>

                  {/* Fused Hero Presentation & Fight Simulator */}
                  {fusedHero && !isFusing && (
                    <div className="bg-[#121722] border-2 border-dashed border-[#1f283a] rounded-xl p-5 flex flex-col md:flex-row items-center justify-between gap-5 animate-fade-in">
                      <div className="flex items-center gap-4">
                        <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-[#1b2230] to-[#0c0f16] flex items-center justify-center text-3xl border border-[#2b354c] relative">
                          {fusedHero.avatar}
                          <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[10px] font-extrabold px-1.5 py-0.5 rounded-md">
                            {fusedHero.rating}
                          </span>
                        </div>
                        <div>
                          <h4 className="text-lg font-bold text-white flex items-center gap-2">
                            {fusedHero.name}
                            <span className="text-[10px] px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded-full font-mono font-normal">
                              {fusedHero.element}
                            </span>
                          </h4>
                          <div className="flex gap-4 text-xs font-mono text-gray-400 mt-1">
                            <span>HP: <strong className="text-rose-400">{fusedHero.hp}</strong></span>
                            <span>ATK: <strong className="text-amber-400">{fusedHero.atk}</strong></span>
                            <span>DEF: <strong className="text-emerald-400">{fusedHero.def}</strong></span>
                          </div>
                        </div>
                      </div>

                      {/* Arena Combat Simulator panel */}
                      <div className="flex flex-col gap-2 w-full md:w-auto">
                        {!isBattling && !battleResult && (
                          <button
                            onClick={handleStartBattle}
                            className={`px-5 py-2 rounded-lg bg-[#1a2233] border border-[#2b354c] text-white font-mono text-xs hover:bg-[#253047] hover:border-gray-500 transition-all flex items-center gap-2 justify-center`}
                          >
                            <Sword size={14} className={currentTheme.text} />
                            Launch Battle Arena Simulation
                          </button>
                        )}

                        {/* Battle Simulation is active */}
                        {(isBattling || battleLogs.length > 0) && (
                          <div className="w-full md:w-[350px] bg-[#090b11] border border-[#1b2230] p-3 rounded-lg flex flex-col gap-3">
                            {/* Health meters */}
                            <div className="flex justify-between items-center text-[10px] font-mono">
                              <div className="flex-1 mr-2">
                                <div className="text-gray-400 flex justify-between">
                                  <span>{fusedHero.name.split(' ')[0]}</span>
                                  <span>{heroHp}/{heroMaxHp}</span>
                                </div>
                                <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden mt-1">
                                  <div className="h-full bg-rose-500 transition-all duration-300" style={{ width: `${(heroHp/heroMaxHp)*100}%` }}></div>
                                </div>
                              </div>
                              <div className="text-gray-500 font-bold px-1">VS</div>
                              <div className="flex-1 ml-2">
                                <div className="text-gray-400 flex justify-between">
                                  <span>{enemyHp}/{enemyMaxHp}</span>
                                  <span>{currentOpponent.split(' ')[0]}</span>
                                </div>
                                <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden mt-1">
                                  <div className="h-full bg-red-500 transition-all duration-300" style={{ width: `${(enemyHp/enemyMaxHp)*100}%` }}></div>
                                </div>
                              </div>
                            </div>

                            {/* Live Scrolling Logs */}
                            <div className="h-24 overflow-y-auto font-mono text-[10px] border border-[#1b2230] p-2 rounded bg-black/40 flex flex-col gap-1 text-gray-300">
                              {battleLogs.map((log, index) => (
                                <div key={index} className="leading-relaxed">{log}</div>
                              ))}
                            </div>

                            {/* Battle Status Indicator */}
                            {battleResult && (
                              <div className="flex items-center justify-between text-xs font-mono mt-1 border-t border-[#1b2230] pt-2">
                                <span className={`font-bold ${battleResult === 'win' ? 'text-emerald-400' : 'text-rose-400'}`}>
                                  {battleResult === 'win' ? '🏆 SIMULATION WIN' : '☠ SIMULATION LOSS'}
                                </span>
                                <button 
                                  onClick={() => { setBattleResult(null); setBattleLogs([]); }} 
                                  className="text-[10px] text-cyan-400 hover:underline"
                                >
                                  Reset Matrix
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 2. App: FusionIsta Molecular Recipe Synthesizer */}
            {activeTab === 'recipe' && (
              <div className="flex-1 flex flex-col justify-between gap-6">
                <div>
                  <h2 className="font-display text-xl font-bold text-white flex items-center gap-2">
                    <ChefHat className={currentTheme.text} />
                    FusionIsta Lab (Molecular Cuisine)
                  </h2>
                  <p className="text-gray-400 text-xs mt-1 font-mono">
                    Harness Gemini AI reasoning (flash-first free tier with Pro fallback when billed) to invent realistic, delicious molecular fusion gastronomy recipes.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-auto">
                  
                  {/* Left Parameter Panel */}
                  <div className="bg-[#121722] border border-[#1f283a] rounded-xl p-4 flex flex-col gap-4">
                    <h3 className="text-xs font-mono tracking-wider text-gray-400 border-b border-[#1f283a] pb-2 uppercase">
                      Fusion Synthesis Parameters
                    </h3>

                    <div className="flex flex-col gap-3 text-xs">
                      {/* Cuisine A select */}
                      <div>
                        <label className="block text-gray-400 mb-1 font-mono">Cuisine Matrix A (Base)</label>
                        <select 
                          value={cuisineA}
                          onChange={(e) => { setCuisineA(e.target.value); playSound('click'); }}
                          className="w-full bg-[#0a0d14] border border-[#2b354c] rounded px-3 py-2 text-white outline-none focus:border-cyan-500 font-mono"
                        >
                          <option value="Japanese">Japanese</option>
                          <option value="Mexican">Mexican</option>
                          <option value="Italian">Italian</option>
                          <option value="Indian">Indian</option>
                          <option value="French">French</option>
                        </select>
                      </div>

                      {/* Cuisine B select */}
                      <div>
                        <label className="block text-gray-400 mb-1 font-mono">Cuisine Matrix B (Twist)</label>
                        <select 
                          value={cuisineB}
                          onChange={(e) => { setCuisineB(e.target.value); playSound('click'); }}
                          className="w-full bg-[#0a0d14] border border-[#2b354c] rounded px-3 py-2 text-white outline-none focus:border-cyan-500 font-mono"
                        >
                          <option value="Mexican">Mexican</option>
                          <option value="Thai">Thai</option>
                          <option value="Ethiopian">Ethiopian</option>
                          <option value="Nordic">Nordic</option>
                          <option value="Peruvian">Peruvian</option>
                          <option value="Greek">Greek</option>
                        </select>
                      </div>

                      {/* Custom Key Ingredient */}
                      <div>
                        <label className="block text-gray-400 mb-1 font-mono">Primary Vector / Ingredient (Optional)</label>
                        <input 
                          type="text" 
                          value={customIngredient}
                          onChange={(e) => setCustomIngredient(e.target.value)}
                          placeholder="e.g. Matcha, Truffle oil, Avocado foam..."
                          className="w-full bg-[#0a0d14] border border-[#2b354c] rounded px-3 py-2 text-white outline-none focus:border-cyan-500 placeholder-gray-600 font-mono"
                        />
                      </div>

                      {/* Scientific Fusion Method */}
                      <div>
                        <label className="block text-gray-400 mb-1 font-mono">Synthesis Methodology</label>
                        <div className="grid grid-cols-2 gap-2 mt-1">
                          {[
                            'Molecular Gastronomy',
                            'Comfort Food Smash',
                            'Deconstructed Elevation',
                            'Fine Dining Emulsion'
                          ].map(method => (
                            <button
                              key={method}
                              onClick={() => { setFusionType(method); playSound('click'); }}
                              className={`p-2 rounded text-[10px] font-mono text-left border transition-all ${
                                fusionType === method 
                                  ? `${currentTheme.bg} ${currentTheme.border} text-white` 
                                  : 'border-[#1b2230] bg-[#0a0d14] text-[#8e98ac] hover:bg-[#121722]'
                              }`}
                            >
                              {method}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Synthesize Button */}
                    <button
                      onClick={handleSynthesizeRecipe}
                      disabled={isSynthesizing}
                      className="w-full py-2.5 rounded-xl bg-cyan-500 text-black font-bold font-mono tracking-widest text-xs uppercase hover:opacity-95 shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-all cursor-pointer flex items-center justify-center gap-2 mt-2 disabled:bg-gray-800 disabled:text-gray-500 disabled:shadow-none"
                    >
                      {isSynthesizing ? (
                        <>
                          <RefreshCw size={14} className="animate-spin" />
                          STIMULATING MOLECULAR SYNTHESIS...
                        </>
                      ) : (
                        <>
                          <Sparkles size={14} />
                          STIMULATE MOLECULAR SYNTHESIS
                        </>
                      )}
                    </button>
                  </div>

                  {/* Right Recipe Card Outcome Panel */}
                  <div className="bg-[#121722] border border-[#1f283a] rounded-xl p-4 flex flex-col justify-center min-h-[300px] relative overflow-hidden">
                    
                    {/* Idle state */}
                    {!isSynthesizing && !generatedRecipe && !recipeError && (
                      <div className="text-center p-6 flex flex-col items-center gap-3 text-gray-500 font-mono">
                        <ChefHat size={40} className="stroke-[1] opacity-40 text-cyan-400" />
                        <p className="text-sm">Lab Reactor Idle</p>
                        <p className="text-[10px] leading-relaxed max-w-xs">
                          Configure the cuisines on the left and start the synthesizer to generate a high-precision molecular dish.
                        </p>
                      </div>
                    )}

                    {/* Loading State with cycling logs */}
                    {isSynthesizing && (
                      <div className="text-center p-6 flex flex-col items-center justify-center gap-4 font-mono animate-pulse">
                        <div className="relative">
                          <div className="w-16 h-16 rounded-full border-4 border-dashed border-cyan-500/20 border-t-cyan-400 animate-spin"></div>
                          <Sparkles className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-cyan-400" size={20} />
                        </div>
                        <div className="flex flex-col gap-1.5">
                          <p className="text-xs font-bold text-white">REACTION MATRIX ACTIVE</p>
                          <p className="text-[10px] text-cyan-400 bg-[#0a0d14] px-3 py-1 rounded-full border border-[#1b2230]">
                            {synthesisLogs}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Error State */}
                    {recipeError && (
                      <div className="p-4 flex flex-col gap-3 text-xs font-mono text-center">
                        <AlertCircle className="text-rose-400 mx-auto" size={32} />
                        <p className="text-white font-bold">SYNTHESIS FAILURE</p>
                        <p className="text-rose-300 bg-rose-500/10 p-3 rounded border border-rose-500/20">
                          {recipeError}
                        </p>
                        <button 
                          onClick={handleSynthesizeRecipe} 
                          className="text-cyan-400 hover:underline mt-2 flex items-center gap-1 justify-center"
                        >
                          <RefreshCw size={12} /> Retry Matrix Core
                        </button>
                      </div>
                    )}

                    {/* Synthesized Recipe Outcome Card */}
                    {generatedRecipe && !isSynthesizing && (
                      <div className="flex flex-col gap-3 text-xs leading-relaxed max-h-[400px] overflow-y-auto pr-1">
                        <div className="border-b border-[#1f283a] pb-2">
                          <div className="flex items-center justify-between text-[10px] font-mono text-cyan-400">
                            <span>FUSION RATIO: {generatedRecipe.fusionRatio}</span>
                            <span className="bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">{generatedRecipe.difficulty}</span>
                          </div>
                          <h4 className="text-base font-bold text-white mt-1">{generatedRecipe.name}</h4>
                          <p className="text-gray-400 italic text-[11px]">{generatedRecipe.tagline}</p>
                        </div>

                        {/* Metadata Row */}
                        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-gray-400 bg-[#0a0d14] p-2 rounded">
                          <div>⏱ PREP: <span className="text-white">{generatedRecipe.prepTime}</span></div>
                          <div>🔥 COOK: <span className="text-white">{generatedRecipe.cookTime}</span></div>
                        </div>

                        {/* Flavors */}
                        <div className="flex flex-wrap gap-1.5">
                          {generatedRecipe.flavorProfile?.map((flavor: string) => (
                            <span key={flavor} className="text-[9px] font-mono px-2 py-0.5 bg-[#1b2230] rounded-full text-gray-300">
                              #{flavor}
                            </span>
                          ))}
                        </div>

                        {/* Ingredients */}
                        <div>
                          <div className="font-mono text-[10px] text-gray-400 uppercase mb-1">Quantum Ingredients</div>
                          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1 font-mono text-[10px] bg-[#0a0d14] p-2.5 rounded border border-[#1b2230]">
                            {generatedRecipe.ingredients?.map((ing: any, i: number) => (
                              <li key={i} className="flex justify-between border-b border-[#121722] pb-0.5 last:border-0 text-gray-300">
                                <span>• {ing.item}</span>
                                <span className="text-cyan-400 text-[8px] uppercase">({ing.category})</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* Methodical Steps */}
                        <div>
                          <div className="font-mono text-[10px] text-gray-400 uppercase mb-1">Chemical Steps / Instructions</div>
                          <div className="flex flex-col gap-2">
                            {generatedRecipe.steps?.map((step: any) => (
                              <div key={step.number} className="bg-[#0c0f16] p-2 rounded border border-[#1b2230] flex gap-2">
                                <span className="font-mono font-bold text-cyan-400 bg-cyan-500/10 w-5 h-5 rounded-full flex items-center justify-center shrink-0">
                                  {step.number}
                                </span>
                                <div>
                                  <div className="font-bold text-white text-[11px]">{step.title}</div>
                                  <p className="text-gray-400 text-[10px] mt-0.5 leading-normal">{step.text}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Chef secret */}
                        {generatedRecipe.chefSecrets && (
                          <div className="bg-[#121926] border border-cyan-500/20 p-2.5 rounded text-[10px]">
                            <strong className="text-cyan-400 block font-mono uppercase mb-0.5">⚛ Molecular Chemical Secret:</strong>
                            <p className="text-gray-300 italic">{generatedRecipe.chefSecrets}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                </div>
              </div>
            )}

            {/* 3. App: AI Intelligence Core */}
            {activeTab === 'ai' && (
              <div className="flex-1 flex flex-col justify-between gap-4">
                <div>
                  <h2 className="font-display text-xl font-bold text-white flex items-center gap-2">
                    <Cpu className={currentTheme.text} />
                    OS Neural Intelligence Core
                  </h2>
                  <p className="text-gray-400 text-xs mt-1 font-mono">
                    Direct stream node using <strong className="text-cyan-400">Gemini reasoning chain</strong> (env-driven flash/Pro with quota fallback) to process heavy logic, code structures, or reasoning.
                  </p>
                </div>

                {/* Chat window viewport */}
                <div className="flex-1 bg-[#090b11] border border-[#1b2230] p-4 rounded-xl flex flex-col gap-3 min-h-[250px] max-h-[350px] overflow-y-auto">
                  {aiMessages.map((msg, idx) => (
                    <div 
                      key={idx} 
                      className={`flex flex-col gap-1 max-w-[85%] ${
                        msg.sender === 'user' ? 'self-end items-end' : 'self-start items-start'
                      }`}
                    >
                      <div className="text-[9px] font-mono text-gray-500 uppercase tracking-widest px-1">
                        {msg.sender === 'user' ? 'OPERATOR' : 'INTELLIGENCE CORE (thinking: HIGH)'}
                      </div>
                      <div 
                        className={`p-3 rounded-xl text-xs leading-relaxed ${
                          msg.sender === 'user' 
                            ? `${currentTheme.bgSolid} text-black font-semibold rounded-tr-none shadow-[0_0_10px_rgba(6,182,212,0.15)]`
                            : 'bg-[#121722] border border-[#1b2230] text-gray-300 rounded-tl-none whitespace-pre-wrap font-mono'
                        }`}
                      >
                        {msg.text}
                      </div>
                    </div>
                  ))}

                  {/* Thinking trace loader */}
                  {isAiThinking && (
                    <div className="self-start flex flex-col gap-1 max-w-[85%] animate-pulse">
                      <div className="text-[9px] font-mono text-cyan-400 uppercase tracking-widest px-1">
                        NEURAL NODE SOLVING EQUATIONS...
                      </div>
                      <div className="p-3 rounded-xl text-xs bg-[#121722] border border-cyan-500/20 text-cyan-400 rounded-tl-none font-mono flex items-center gap-2">
                        <RefreshCw className="animate-spin" size={13} />
                        Synthesizing step-by-step logic. Please hold terminal sync...
                      </div>
                    </div>
                  )}

                  {aiError && (
                    <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 font-mono text-xs flex items-center gap-2">
                      <AlertCircle size={14} />
                      {aiError}
                    </div>
                  )}
                </div>

                {/* Input node console */}
                <div className="flex gap-2">
                  <input 
                    type="text"
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSendAiMessage(); }}
                    placeholder="Enter complex mathematical formula, logic riddle, or system request..."
                    className="flex-1 bg-[#090b11] border border-[#1b2230] rounded-xl px-4 py-3 text-xs outline-none focus:border-cyan-500 text-white font-mono placeholder-gray-600"
                    disabled={isAiThinking}
                  />
                  <button
                    onClick={handleSendAiMessage}
                    disabled={!aiInput.trim() || isAiThinking}
                    className={`p-3 rounded-xl transition-all cursor-pointer ${
                      aiInput.trim() && !isAiThinking 
                        ? `${currentTheme.bgSolid} text-black shadow-[0_0_12px_currentColor] hover:opacity-90` 
                        : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <Send size={15} />
                  </button>
                </div>
              </div>
            )}

            {/* 🧪 Neural Labs Matrix */}
            {activeTab === 'labs' && (
              <div className="flex-1 flex flex-col justify-between gap-5 text-xs font-sans min-h-[500px]">
                {/* Header section */}
                <div>
                  <h2 className="font-display text-xl font-bold text-white flex items-center gap-2">
                    <Sparkles className="text-pink-400 animate-pulse" />
                    Neural Labs Multimedia & Grounding Matrix
                  </h2>
                  <p className="text-gray-400 text-xs mt-1 font-mono">
                    Integrated gateway for Grounded Search, Voice synthesis, Lyria Music, Veo Video rendering, and high fidelity Image generation.
                  </p>
                </div>

                {/* Sub-navigation inside Labs */}
                <div className="flex gap-2 border-b border-[#1b2230] pb-2">
                  <button
                    onClick={() => { setLabsSubTab('chat'); playSound('click'); }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-mono text-[11px] transition-all border ${
                      labsSubTab === 'chat'
                        ? 'border-pink-500/30 bg-pink-500/10 text-pink-400'
                        : 'border-transparent text-gray-400 hover:text-white'
                    }`}
                  >
                    <Cpu size={12} /> Grounding Chat
                  </button>

                  <button
                    onClick={() => { setLabsSubTab('media'); playSound('click'); }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-mono text-[11px] transition-all border ${
                      labsSubTab === 'media'
                        ? 'border-cyan-500/30 bg-cyan-500/10 text-cyan-400'
                        : 'border-transparent text-gray-400 hover:text-white'
                    }`}
                  >
                    <Image size={12} /> Media Gen & Analysis
                  </button>

                  <button
                    onClick={() => { setLabsSubTab('audio'); playSound('click'); }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-mono text-[11px] transition-all border ${
                      labsSubTab === 'audio'
                        ? 'border-purple-500/30 bg-purple-500/10 text-purple-400'
                        : 'border-transparent text-gray-400 hover:text-white'
                    }`}
                  >
                    <Music size={12} /> Sonic Synthesis
                  </button>
                </div>

                {/* Content body based on subtab */}
                <div className="flex-1 bg-[#090b11] border border-[#1b2230] rounded-xl p-4 flex flex-col gap-4 overflow-y-auto max-h-[500px]">
                  
                  {/* SUBTAB 1: Grounded Chat & Core */}
                  {labsSubTab === 'chat' && (
                    <div className="flex-1 flex flex-col gap-3 min-h-[350px]">
                      {/* Configuration bar */}
                      <div className="flex flex-wrap gap-2 items-center justify-between border-b border-[#1b2230] pb-2 text-[11px]">
                        <span className="font-mono text-gray-400">ENGINE PROFILE:</span>
                        <div className="flex flex-wrap gap-1">
                          {(['high-thinking', 'low-latency', 'search-grounding', 'maps-grounding'] as const).map(mode => (
                            <button
                              key={mode}
                              onClick={() => { setLabsChatMode(mode); playSound('click'); }}
                              className={`px-2 py-1 rounded font-mono text-[10px] uppercase border transition-all ${
                                labsChatMode === mode
                                  ? 'border-pink-500/40 bg-pink-500/10 text-pink-400'
                                  : 'border-transparent bg-[#121722] text-gray-400 hover:text-white'
                              }`}
                            >
                              {mode === 'high-thinking' && '🧠 High Thinking'}
                              {mode === 'low-latency' && '⚡ Low Latency'}
                              {mode === 'search-grounding' && '🌐 Google Search'}
                              {mode === 'maps-grounding' && '📍 Google Maps'}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Chat messages stream */}
                      <div className="flex-1 flex flex-col gap-3 min-h-[200px] max-h-[300px] overflow-y-auto bg-[#06080d] p-3 rounded-lg border border-[#121722]">
                        {labsChatMessages.map((msg, idx) => (
                          <div
                            key={idx}
                            className={`flex flex-col gap-1 max-w-[85%] ${
                              msg.sender === 'user' ? 'self-end items-end' : 'self-start items-start'
                            }`}
                          >
                            <span className="text-[9px] font-mono text-gray-500 uppercase tracking-wider px-1">
                              {msg.sender === 'user' ? 'OPERATOR' : `NODE MATRIX (${msg.mode || 'ACTIVE'})`}
                            </span>
                            <div
                              className={`p-3 rounded-xl leading-relaxed whitespace-pre-wrap font-mono ${
                                msg.sender === 'user'
                                  ? `${currentTheme.bgSolid} text-black font-semibold rounded-tr-none`
                                  : 'bg-[#121722] border border-[#1b2230] text-gray-300 rounded-tl-none'
                              }`}
                            >
                              {msg.text}

                              {/* Search Grounding citation chunks rendering */}
                              {msg.groundingChunks && msg.groundingChunks.length > 0 && (
                                <div className="mt-2 pt-2 border-t border-gray-800 text-[10px] text-gray-400">
                                  <div className="font-bold text-pink-400 uppercase tracking-widest text-[8px] mb-1">🌐 Cited Sources (Google Search Grounding)</div>
                                  <ul className="flex flex-col gap-1">
                                    {msg.groundingChunks.map((chunk, cidx) => (
                                      <li key={cidx} className="flex gap-1 items-start bg-black/40 p-1.5 rounded">
                                        <span className="bg-pink-500/20 text-pink-300 font-bold px-1 rounded text-[8px] mt-0.5">{cidx + 1}</span>
                                        <div>
                                          <div className="text-white font-semibold text-[9px]">{chunk.title}</div>
                                          <a href={chunk.uri} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline break-all text-[8px] block">
                                            {chunk.uri}
                                          </a>
                                        </div>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}

                        {isLabsChatLoading && (
                          <div className="self-start flex flex-col gap-1 animate-pulse max-w-[85%]">
                            <span className="text-[9px] font-mono text-pink-400 uppercase tracking-wider">RESOLVING MATRIX FLOW...</span>
                            <div className="p-3 bg-[#121722] border border-pink-500/20 text-pink-400 rounded-tl-none rounded-xl font-mono flex items-center gap-2">
                              <RefreshCw className="animate-spin text-pink-400" size={13} />
                              Syncing neural network parameters...
                            </div>
                          </div>
                        )}

                        {labsChatError && (
                          <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 font-mono text-xs flex items-center gap-2">
                            <AlertCircle size={14} />
                            {labsChatError}
                          </div>
                        )}
                      </div>

                      {/* Chat input form */}
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={labsChatInput}
                          onChange={(e) => setLabsChatInput(e.target.value)}
                          onKeyDown={(e) => { if (e.key === 'Enter') handleSendLabsChatMessage(); }}
                          placeholder={
                            labsChatMode === 'search-grounding' ? "Query Google Search grounding (e.g. Current stock values, weather)..." :
                            labsChatMode === 'maps-grounding' ? "Query nearby points or address validations via Google Maps..." :
                            "Submit complex query to grounding engine..."
                          }
                          className="flex-1 bg-[#090b11] border border-[#1b2230] rounded-xl px-4 py-3 text-xs outline-none focus:border-pink-500 text-white font-mono placeholder-gray-600"
                          disabled={isLabsChatLoading}
                        />
                        <button
                          onClick={handleSendLabsChatMessage}
                          disabled={!labsChatInput.trim() || isLabsChatLoading}
                          className={`p-3 rounded-xl transition-all cursor-pointer ${
                            labsChatInput.trim() && !isLabsChatLoading
                              ? 'bg-pink-500 text-black font-bold hover:bg-pink-400 shadow-[0_0_12px_rgba(244,63,94,0.3)]'
                              : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                          }`}
                        >
                          <Send size={15} />
                        </button>
                      </div>
                    </div>
                  )}

                  {/* SUBTAB 2: Image Gen, Video Gen, Media multimodal Analysis */}
                  {labsSubTab === 'media' && (
                    <div className="flex flex-col gap-5">
                      
                      {/* Section A: Image Gen */}
                      <div className="bg-[#0c1018] border border-[#1b2230] p-4 rounded-xl flex flex-col gap-3">
                        <h3 className="font-mono text-xs font-bold text-white flex items-center gap-1 border-b border-[#121722] pb-1.5 uppercase">
                          <Image size={13} className="text-cyan-400" /> Image Generation (gemini-3.1-flash-image)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="flex flex-col gap-2.5">
                            <label className="text-[10px] font-mono text-gray-400 uppercase">Interactive Prompt</label>
                            <textarea
                              value={imagePrompt}
                              onChange={(e) => setImagePrompt(e.target.value)}
                              rows={2}
                              className="bg-[#06080d] border border-[#1f283a] p-2.5 rounded font-mono text-xs text-white outline-none focus:border-cyan-500 resize-none"
                            />

                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Aspect Ratio</label>
                                <select
                                  value={imageAspectRatio}
                                  onChange={(e) => setImageAspectRatio(e.target.value)}
                                  className="w-full bg-[#06080d] border border-[#1f283a] p-1.5 rounded font-mono text-[11px] text-white focus:border-cyan-500 outline-none"
                                >
                                  {['1:1', '3:2', '2:3', '3:4', '4:3', '9:16', '16:9', '21:9'].map(ratio => (
                                    <option key={ratio} value={ratio}>{ratio}</option>
                                  ))}
                                </select>
                              </div>
                              <div>
                                <label className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Fidelity Size</label>
                                <select
                                  value={imageSize}
                                  onChange={(e) => setImageSize(e.target.value)}
                                  className="w-full bg-[#06080d] border border-[#1f283a] p-1.5 rounded font-mono text-[11px] text-white focus:border-cyan-500 outline-none"
                                >
                                  <option value="1K">1K UHD Standard</option>
                                  <option value="2K">2K QuadHD Extreme</option>
                                  <option value="4K">4K UltraHD Master</option>
                                </select>
                              </div>
                            </div>

                            <button
                              onClick={handleGenerateImage}
                              disabled={isGeneratingImage || !imagePrompt.trim()}
                              className="w-full bg-cyan-500 text-black font-bold py-2 rounded font-mono text-xs hover:opacity-90 transition-all flex items-center justify-center gap-1.5 mt-1"
                            >
                              {isGeneratingImage ? <RefreshCw className="animate-spin" size={13} /> : <Sparkles size={13} />}
                              {isGeneratingImage ? 'Synthesizing Image Canvas...' : 'Generate Neural Image'}
                            </button>
                            {imageError && (
                              <div className="text-[10px] text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20 font-mono mt-1">
                                {imageError}
                              </div>
                            )}
                          </div>

                          {/* Image preview canvas */}
                          <div className="bg-[#06080d] border border-[#1f283a] rounded-lg p-2 flex items-center justify-center relative min-h-[160px]">
                            {isGeneratingImage ? (
                              <div className="flex flex-col items-center gap-2 text-center text-[10px] text-cyan-400 font-mono">
                                <RefreshCw className="animate-spin text-cyan-400" size={24} />
                                <span className="animate-pulse">Rasterizing virtual pixels...</span>
                              </div>
                            ) : generatedImageUrl ? (
                              <div className="relative group w-full h-full flex items-center justify-center overflow-hidden rounded">
                                <img
                                  src={generatedImageUrl}
                                  alt="AI Generated"
                                  referrerPolicy="no-referrer"
                                  className="max-h-[180px] object-contain rounded transition-transform group-hover:scale-105"
                                />
                                <a
                                  href={generatedImageUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="absolute bottom-2 right-2 bg-black/70 hover:bg-black/90 text-[9px] text-cyan-400 px-2 py-1 rounded font-mono border border-cyan-500/20"
                                >
                                  Open Original
                                </a>
                              </div>
                            ) : (
                              <span className="text-gray-600 font-mono text-[10px]">No image canvas compiled.</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Section B: Multimodal Media Analysis */}
                      <div className="bg-[#0c1018] border border-[#1b2230] p-4 rounded-xl flex flex-col gap-3">
                        <h3 className="font-mono text-xs font-bold text-white flex items-center gap-1 border-b border-[#121722] pb-1.5 uppercase">
                          <Search size={13} className="text-cyan-400" /> Multimodal Telemetry Analysis
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="flex flex-col gap-2.5">
                            <label className="text-[10px] font-mono text-gray-400 uppercase">1. Choose Telemetry File (PNG, JPG, PDF, WEBP)</label>
                            <input
                              type="file"
                              accept="image/*,application/pdf"
                              onChange={handleMediaUploadChange}
                              className="bg-[#06080d] border border-[#1f283a] rounded p-2 text-xs text-gray-400 font-mono w-full"
                            />

                            <label className="text-[10px] font-mono text-gray-400 uppercase">2. Custom Analysis Prompt</label>
                            <input
                              type="text"
                              value={mediaAnalysisPrompt}
                              onChange={(e) => setMediaAnalysisPrompt(e.target.value)}
                              className="bg-[#06080d] border border-[#1f283a] p-2 rounded text-xs text-white font-mono"
                            />

                            <button
                              onClick={handleAnalyzeMedia}
                              disabled={isAnalyzingMedia || !uploadedMedia}
                              className={`w-full font-bold py-2 rounded font-mono text-xs transition-all flex items-center justify-center gap-1.5 ${
                                uploadedMedia && !isAnalyzingMedia
                                  ? 'bg-cyan-500 text-black hover:opacity-90'
                                  : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                              }`}
                            >
                              {isAnalyzingMedia ? <RefreshCw className="animate-spin" size={13} /> : <Search size={13} />}
                              Analyze File Stream
                            </button>
                            {mediaAnalysisError && (
                              <div className="text-[10px] text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20 font-mono">
                                {mediaAnalysisError}
                              </div>
                            )}
                          </div>

                          <div className="bg-[#06080d] border border-[#1f283a] rounded-lg p-3 min-h-[160px] max-h-[180px] overflow-y-auto">
                            <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider block mb-1">Analysis Telemetry:</span>
                            {isAnalyzingMedia ? (
                              <div className="flex flex-col items-center gap-1 text-center py-6">
                                <RefreshCw className="animate-spin text-cyan-400" size={16} />
                                <span className="font-mono text-[9px] text-gray-500">Decompiling file vectors...</span>
                              </div>
                            ) : mediaAnalysisResult ? (
                              <p className="text-[11px] leading-relaxed text-gray-300 font-mono whitespace-pre-wrap">{mediaAnalysisResult}</p>
                            ) : uploadedMedia ? (
                              <div className="text-center py-6 flex flex-col items-center gap-1.5">
                                <div className="text-emerald-400 text-xs font-mono">✓ TELEMETRY LOADED</div>
                                <span className="text-[9px] text-gray-500 font-mono">Click "Analyze File Stream" to process.</span>
                              </div>
                            ) : (
                              <span className="text-gray-600 font-mono text-[10px] block py-6 text-center">Upload telemetry files to begin matrix audit.</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Section C: Video Gen */}
                      <div className="bg-[#0c1018] border border-[#1b2230] p-4 rounded-xl flex flex-col gap-3">
                        <h3 className="font-mono text-xs font-bold text-white flex items-center gap-1 border-b border-[#121722] pb-1.5 uppercase">
                          <Video size={13} className="text-cyan-400" /> Video Reactor Engine (Veo 3.1 Lite)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="flex flex-col gap-2.5">
                            <label className="text-[10px] font-mono text-gray-400 uppercase">Video Scenic Description</label>
                            <textarea
                              value={videoPrompt}
                              onChange={(e) => setVideoPrompt(e.target.value)}
                              rows={2}
                              className="bg-[#06080d] border border-[#1f283a] p-2.5 rounded font-mono text-xs text-white outline-none focus:border-cyan-500 resize-none"
                            />

                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Layout</label>
                                <select
                                  value={videoAspectRatio}
                                  onChange={(e) => setVideoAspectRatio(e.target.value)}
                                  className="w-full bg-[#06080d] border border-[#1f283a] p-1.5 rounded font-mono text-[11px] text-white focus:border-cyan-500 outline-none"
                                >
                                  <option value="16:9">Widescreen 16:9</option>
                                  <option value="9:16">Vertical 9:16</option>
                                </select>
                              </div>
                              <div>
                                <label className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Resolution</label>
                                <select
                                  value={videoResolution}
                                  onChange={(e) => setVideoResolution(e.target.value)}
                                  className="w-full bg-[#06080d] border border-[#1f283a] p-1.5 rounded font-mono text-[11px] text-white focus:border-cyan-500 outline-none"
                                >
                                  <option value="720p">720p HD</option>
                                  <option value="1080p">1080p UltraHD</option>
                                </select>
                              </div>
                            </div>

                            <button
                              onClick={handleGenerateVideo}
                              disabled={videoGenerationStatus === 'generating' || videoGenerationStatus === 'polling' || !videoPrompt.trim()}
                              className="w-full bg-cyan-500 text-black font-bold py-2 rounded font-mono text-xs hover:opacity-90 transition-all flex items-center justify-center gap-1.5 mt-1"
                            >
                              {(videoGenerationStatus === 'generating' || videoGenerationStatus === 'polling') ? (
                                <RefreshCw className="animate-spin" size={13} />
                              ) : (
                                <Play size={13} />
                              )}
                              {(videoGenerationStatus === 'generating' || videoGenerationStatus === 'polling') ? 'Processing video vectors...' : 'Initiate Veo 3.1 Loop'}
                            </button>
                            {videoError && (
                              <div className="text-[10px] text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20 font-mono mt-1">
                                {videoError}
                              </div>
                            )}
                          </div>

                          {/* Video output viewer */}
                          <div className="bg-[#06080d] border border-[#1f283a] rounded-lg p-2 flex flex-col items-center justify-center relative min-h-[160px]">
                            {(videoGenerationStatus === 'generating' || videoGenerationStatus === 'polling') ? (
                              <div className="flex flex-col items-center gap-2.5 text-center p-4">
                                <RefreshCw className="animate-spin text-cyan-400" size={24} />
                                <span className="text-[10px] font-mono text-cyan-400 animate-pulse font-bold">{videoLogs}</span>
                                <span className="text-[9px] font-mono text-gray-500">Veo operations are heavy async tasks. Sync takes 20-30 seconds. Please preserve link.</span>
                              </div>
                            ) : generatedVideoUrl ? (
                              <video
                                src={generatedVideoUrl}
                                controls
                                autoPlay
                                loop
                                className="max-h-[180px] w-full object-contain rounded"
                              />
                            ) : (
                              <span className="text-gray-600 font-mono text-[10px]">No Video stream initialized.</span>
                            )}
                          </div>
                        </div>
                      </div>

                    </div>
                  )}

                  {/* SUBTAB 3: Sonic Voice Speech synthesis, Audio transcription, and Lyria Music */}
                  {labsSubTab === 'audio' && (
                    <div className="flex flex-col gap-5">
                      
                      {/* Section A: Text to Speech Speech Synthesis */}
                      <div className="bg-[#0c1018] border border-[#1b2230] p-4 rounded-xl flex flex-col gap-3">
                        <h3 className="font-mono text-xs font-bold text-white flex items-center gap-1 border-b border-[#121722] pb-1.5 uppercase">
                          <Mic size={13} className="text-purple-400" /> Voice Synthesis Node
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="flex flex-col gap-2.5">
                            <label className="text-[10px] font-mono text-gray-400 uppercase">Input Script (TTS)</label>
                            <input
                              type="text"
                              value={ttsInputText}
                              onChange={(e) => setTtsInputText(e.target.value)}
                              className="bg-[#06080d] border border-[#1f283a] p-2 rounded text-xs text-white font-mono"
                            />

                            <div>
                              <label className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Synthesizer Voice Profile</label>
                              <select
                                value={ttsVoice}
                                onChange={(e) => setTtsVoice(e.target.value)}
                                className="w-full bg-[#06080d] border border-[#1f283a] p-1.5 rounded font-mono text-[11px] text-white focus:border-purple-500 outline-none"
                              >
                                {['Puck', 'Charon', 'Kore', 'Fenrir', 'Zephyr'].map(voice => (
                                  <option key={voice} value={voice}>{voice}</option>
                                ))}
                              </select>
                            </div>

                            <button
                              onClick={handleTtsGenerate}
                              disabled={isTtsLoading || !ttsInputText.trim()}
                              className="w-full bg-purple-500 text-black font-bold py-2 rounded font-mono text-xs hover:opacity-90 transition-all flex items-center justify-center gap-1.5 mt-1"
                            >
                              {isTtsLoading ? <RefreshCw className="animate-spin" size={13} /> : <Volume2 size={13} />}
                              Synthesize Voice Speech
                            </button>
                            {ttsError && (
                              <div className="text-[10px] text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20 font-mono">
                                {ttsError}
                              </div>
                            )}
                          </div>

                          {/* Sound preview block */}
                          <div className="bg-[#06080d] border border-[#1f283a] rounded-lg p-4 flex flex-col justify-center items-center">
                            {isTtsLoading ? (
                              <div className="flex flex-col items-center gap-1.5 text-center">
                                <RefreshCw className="animate-spin text-purple-400" size={18} />
                                <span className="font-mono text-[9px] text-gray-500">Synthesizing vocal patterns...</span>
                              </div>
                            ) : generatedTtsUrl ? (
                              <div className="w-full flex flex-col gap-2">
                                <span className="text-[10px] font-mono text-purple-400 text-center font-bold">✓ AUDIO WAVEFORM PREPARED</span>
                                <audio src={generatedTtsUrl} controls className="w-full h-8" />
                              </div>
                            ) : (
                              <span className="text-gray-600 font-mono text-[10px]">No vocal wave generated.</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Section B: Lyria Music Generation */}
                      <div className="bg-[#0c1018] border border-[#1b2230] p-4 rounded-xl flex flex-col gap-3">
                        <h3 className="font-mono text-xs font-bold text-white flex items-center gap-1 border-b border-[#121722] pb-1.5 uppercase">
                          <Music size={13} className="text-purple-400" /> Lyria Music Composition (lyria-3-pro)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="flex flex-col gap-2.5">
                            <label className="text-[10px] font-mono text-gray-400 uppercase">Music Theme or Lyrics Prompt</label>
                            <textarea
                              value={musicPrompt}
                              onChange={(e) => setMusicPrompt(e.target.value)}
                              rows={2}
                              className="bg-[#06080d] border border-[#1f283a] p-2.5 rounded font-mono text-xs text-white outline-none focus:border-purple-500 resize-none"
                            />

                            <div>
                              <label className="text-[9px] font-mono text-gray-500 uppercase block mb-1">Composition Length</label>
                              <select
                                value={musicLength}
                                onChange={(e) => setMusicLength(e.target.value)}
                                className="w-full bg-[#06080d] border border-[#1f283a] p-1.5 rounded font-mono text-[11px] text-white focus:border-purple-500 outline-none"
                              >
                                <option value="short">Short clip (8 seconds loops)</option>
                                <option value="full">Full length (30-60 seconds thematic master)</option>
                              </select>
                            </div>

                            <button
                              onClick={handleGenerateMusic}
                              disabled={isGeneratingMusic || !musicPrompt.trim()}
                              className="w-full bg-purple-500 text-black font-bold py-2 rounded font-mono text-xs hover:opacity-90 transition-all flex items-center justify-center gap-1.5 mt-1"
                            >
                              {isGeneratingMusic ? <RefreshCw className="animate-spin" size={13} /> : <Sparkles size={13} />}
                              Compose Lyria Melody
                            </button>
                            {musicError && (
                              <div className="text-[10px] text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20 font-mono">
                                {musicError}
                              </div>
                            )}
                          </div>

                          {/* Music preview block */}
                          <div className="bg-[#06080d] border border-[#1f283a] rounded-lg p-4 flex flex-col justify-center items-center min-h-[160px] max-h-[180px] overflow-y-auto">
                            {isGeneratingMusic ? (
                              <div className="flex flex-col items-center gap-2 text-center">
                                <RefreshCw className="animate-spin text-purple-400" size={20} />
                                <span className="font-mono text-[10px] text-purple-400 animate-pulse">Orchestrating musical notes...</span>
                              </div>
                            ) : generatedMusicUrl ? (
                              <div className="w-full flex flex-col gap-3">
                                <div className="text-center">
                                  <span className="text-[10px] font-mono text-purple-400 font-bold">✓ COMPOSITION RENDERING COMPLETE</span>
                                  <audio src={generatedMusicUrl} controls className="w-full h-8 mt-1" />
                                </div>
                                {generatedMusicLyrics && (
                                  <div className="bg-black/50 p-2 rounded text-[10px] border border-[#121722] font-mono">
                                    <div className="text-[8px] uppercase font-bold text-purple-300 tracking-wider mb-1">Generated Lyrics Matrix:</div>
                                    <p className="text-gray-300 italic whitespace-pre-wrap leading-relaxed">{generatedMusicLyrics}</p>
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-600 font-mono text-[10px]">No symphonic notes composed.</span>
                            )}
                          </div>
                        </div>
                      </div>

                    </div>
                  )}

                </div>
              </div>
            )}

            {/* 4. App: Environment Files Explorer */}
            {activeTab === 'files' && (
              <div className="flex-1 flex flex-col gap-5">
                <div>
                  <h2 className="font-display text-xl font-bold text-white flex items-center gap-2">
                    <Folder className={currentTheme.text} />
                    Host Workspace Explorer
                  </h2>
                  <p className="text-gray-400 text-xs mt-1 font-mono">
                    Review and verify the actual runtime configuration scripts. Fully responsive, local container nodes.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 flex-1">
                  
                  {/* File Directory list */}
                  <div className="bg-[#121722] border border-[#1f283a] p-3 rounded-xl flex flex-col gap-1.5 font-mono text-xs max-h-[250px] overflow-y-auto">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2 border-b border-[#1f283a] pb-1">
                      Host Workspace Tree
                    </div>
                    {(workspaceFiles.length > 0 ? workspaceFiles : SAMPLE_FILES).map(file => (
                      <button
                        key={file.name}
                        onClick={() => { setSelectedFile(file.name); playSound('click'); }}
                        className={`flex items-center justify-between p-2 rounded transition-all text-left ${
                          selectedFile === file.name 
                            ? `${currentTheme.bg} ${currentTheme.border} text-white` 
                            : 'text-[#8e98ac] hover:bg-[#0c1018]'
                        }`}
                      >
                        <span className="flex items-center gap-1.5 truncate">
                          <FileCode size={13} className={selectedFile === file.name ? currentTheme.text : 'text-gray-500'} />
                          {file.name}
                        </span>
                        <span className="text-[9px] opacity-60 text-gray-400">{file.size}</span>
                      </button>
                    ))}
                  </div>

                  {/* Syntactical view panel */}
                  <div className="bg-[#090b11] border border-[#1f283a] p-4 rounded-xl md:col-span-2 font-mono text-[10px] leading-relaxed max-h-[250px] overflow-y-auto overflow-x-auto text-gray-400">
                    <div className="text-gray-500 border-b border-[#1f283a] pb-1.5 mb-2 flex items-center justify-between">
                      <span>FILE PREVIEW // {selectedFile}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase border ${
                        isLoadingFiles 
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' 
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      }`}>
                        {isLoadingFiles ? 'LOADING...' : 'LIVE'}
                      </span>
                    </div>

                    {(() => {
                      const foundFile = workspaceFiles.find(f => f.name === selectedFile);
                      if (foundFile) {
                        return (
                          <pre className="whitespace-pre text-left">
                            {foundFile.content}
                          </pre>
                        );
                      }

                      if (selectedFile === 'App.tsx') {
                        return (
                          <pre className="whitespace-pre">
{`import { useState } from 'react';
import { Terminal, ChefHat, Cpu } from 'lucide-react';

// Core OS View controllers and fusion engines
export default function App() {
  const [activeTab, setActiveTab] = useState('battler');
  const [accentColor, setAccentColor] = useState('cyan');
  
  return (
    <div className="min-h-screen bg-[#0a0c10]">
      {/* Dynamic Workspace Framework */}
    </div>
  );
}`}
                          </pre>
                        );
                      }

                      if (selectedFile === 'server.ts') {
                        return (
                          <pre className="whitespace-pre">
{`import express from 'express';
import { GoogleGenAI, ThinkingLevel } from '@google/genai';

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

// High-thinking reasoning endpoint
app.post('/api/gemini/thinking', async (req, res) => {
  const { message } = req.body;
  const response = await ai.models.generateContent({
    model: 'gemini-3.1-pro-preview',
    contents: message,
    config: { thinkingConfig: { thinkingLevel: ThinkingLevel.HIGH } }
  });
  res.json({ text: response.text });
});`}
                          </pre>
                        );
                      }

                      if (selectedFile === 'package.json') {
                        return (
                          <pre className="whitespace-pre">
{`{
  "name": "fusion-hero-os",
  "version": "4.1.0",
  "type": "module",
  "scripts": {
    "dev": "tsx server.ts",
    "start": "node server.ts",
    "build": "vite build"
  },
  "dependencies": {
    "@google/genai": "^2.4.0",
    "express": "^4.21.2"
  }
}`}
                          </pre>
                        );
                      }

                      if (selectedFile === 'index.html') {
                        return (
                          <pre className="whitespace-pre">
{`<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Fusion Hero OS Desktop</title>
  </head>
  <body class="bg-[#0a0c10]">
    <div id="root"></div>
  </body>
</html>`}
                          </pre>
                        );
                      }

                      if (selectedFile === 'metadata.json') {
                        return (
                          <pre className="whitespace-pre">
{`{
  "name": "Fusion Hero OS Desktop",
  "description": "A high-fidelity responsive simulator combining auto-battlers and high-thinking models.",
  "majorCapabilities": ["MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API"]
}`}
                          </pre>
                        );
                      }

                      return <span className="text-gray-500">File content not loaded.</span>;
                    })()}
                  </div>

                </div>
              </div>
            )}

            {/* 5. App: About OS */}
            {activeTab === 'about' && (
              <div className="flex-1 flex flex-col justify-between gap-5 font-mono text-xs leading-relaxed text-gray-300">
                <div>
                  <h2 className="font-display text-xl font-bold text-white flex items-center gap-2">
                    <HelpCircle className={currentTheme.text} />
                    Fusion Hero OS // Architectural Outline
                  </h2>
                  <p className="text-gray-400 text-xs mt-1">
                    System core configuration specs, layout metrics, and framework information.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-auto bg-[#121722] p-5 rounded-xl border border-[#1f283a]">
                  <div>
                    <h4 className="text-white font-bold mb-2 flex items-center gap-1.5">
                      <Cpu size={14} className={currentTheme.text} />
                      AI Capabilities (Neural Core)
                    </h4>
                    <p className="text-gray-400 text-[11px] leading-relaxed">
                      Powered by the server-side Google GenAI SDK with an <strong className="text-cyan-400">env-driven reasoning chain</strong> (flash-first free tier, optional Pro + ThinkingLevel.HIGH when billed).
                    </p>
                  </div>

                  <div>
                    <h4 className="text-white font-bold mb-2 flex items-center gap-1.5">
                      <Layers size={14} className={currentTheme.text} />
                      Simulated Roguelike Matrix
                    </h4>
                    <p className="text-gray-400 text-[11px] leading-relaxed">
                      Integrates deep auto-battler variables mimicking tactical gameplay logic. Features HP/ATK multipliers, random critical strike models, dynamic evasion arrays, and recursive combat algorithms.
                    </p>
                  </div>

                  <div>
                    <h4 className="text-white font-bold mb-2 flex items-center gap-1.5">
                      <ChefHat size={14} className={currentTheme.text} />
                      FusionIsta Lab Synthesis
                    </h4>
                    <p className="text-gray-400 text-[11px] leading-relaxed">
                      Merges two opposing flavor palettes into a molecular cooking instruction index. Utilizes prompt engineering models to enforce physical culinary logic without generating mock values.
                    </p>
                  </div>

                  <div>
                    <h4 className="text-white font-bold mb-2 flex items-center gap-1.5">
                      <Settings size={14} className={currentTheme.text} />
                      Desktop Responsive Matrix
                    </h4>
                    <p className="text-gray-400 text-[11px] leading-relaxed">
                      Designed to adjust layout proportions automatically inside compressed iframe portals or expanded ultra-wide viewports. Uses Tailwind grids and CSS transitions for clean desktop fidelity.
                    </p>
                  </div>
                </div>

                <div className="text-[10px] text-gray-500 text-center border-t border-[#1b2230] pt-3">
                  Fusion Hero OS v4.1.0 • Built with TypeScript • Tailwind CSS • Google AI Studio
                </div>
              </div>
            )}

            {/* Outer Frame Glow Accents */}
            <div className={`absolute inset-0 pointer-events-none rounded-xl border border-transparent transition-all duration-500 ${currentTheme.border} ${currentTheme.borderGlow}`}></div>
          </div>
        </section>

        {/* Right Side: Cybernetic Control Console Terminal Panel */}
        <aside className="w-full lg:w-[350px] border-t lg:border-t-0 lg:border-l border-[#1b2230] bg-[#090b11] p-4 lg:p-6 flex flex-col gap-4">
          
          {/* Subsystem Coordinates Monitor */}
          <div className="bg-[#0b0e16] border border-[#1b2230] rounded-xl p-4 flex flex-col gap-2.5 font-mono text-xs">
            <h3 className="text-[10px] text-gray-500 tracking-wider uppercase border-b border-[#1b2230] pb-1 flex items-center gap-1.5">
              <Settings size={12} className={currentTheme.text} />
              WORKSPACE CONTROLLERS
            </h3>
            
            <div className="flex flex-col gap-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-gray-400">Environment Node:</span>
                <span className="text-white">Cloud Container</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Port Allocator:</span>
                <span className="text-cyan-400 font-bold">3000 (Proxy Target)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Sonic Feedback:</span>
                <span className={soundEnabled ? 'text-emerald-400 font-bold' : 'text-gray-500'}>
                  {soundEnabled ? 'ENABLED' : 'DISABLED'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">UI Accent Wave:</span>
                <span className="text-white capitalize font-bold">{accentColor}</span>
              </div>
            </div>
          </div>

          {/* Scrolling Terminal Logger */}
          <div className="flex-1 bg-black border border-[#1b2230] rounded-xl p-4 flex flex-col gap-2 font-mono text-[10px] overflow-hidden min-h-[180px] max-h-[300px] lg:max-h-none">
            <div className="text-gray-500 border-b border-[#1b2230] pb-1 flex items-center justify-between uppercase tracking-wider">
              <span>System Core Console Logs</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            </div>

            <div className="flex-1 overflow-y-auto flex flex-col gap-1.5 text-[#a8b2d1] pr-1 leading-relaxed">
              {terminalLogs.map((log, index) => (
                <div key={index} className="break-words">
                  {log}
                </div>
              ))}
              <div ref={logsEndRef}></div>
            </div>

            {/* Quick terminal execute bar */}
            <div className="border-t border-[#1b2230] pt-2 flex items-center gap-1.5 text-gray-500">
              <span className={currentTheme.text}>$</span>
              <input 
                type="text" 
                placeholder="OS diagnostics waiting..."
                disabled
                className="bg-transparent text-[#cfd4de] text-[10px] outline-none flex-1 placeholder-gray-700 italic cursor-not-allowed"
              />
            </div>
          </div>
        </aside>

      </main>

      {/* 🔮 Dock / Taskbar Footer */}
      <footer className="border-t border-[#1b2230] bg-[#06080d] px-4 py-3 flex flex-col sm:flex-row items-center justify-between text-[11px] font-mono text-gray-500 gap-2">
        <div>
          Operator Sync: <strong className="text-gray-300">user@example.com</strong>
        </div>
        <div className="flex items-center gap-4">
          <span>Google Gemini Pro Thinking Level: <strong className="text-cyan-400">HIGH</strong></span>
          <span className="text-gray-700">|</span>
          <span className="text-gray-400">AISTUDIO_BUILD // ACTIVE</span>
        </div>
      </footer>

    </div>
  );
}
