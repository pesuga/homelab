"use client";

import React, { useState, useEffect, createContext, useContext } from "react";
import { useAuth } from "@/context/AuthContext";

// Types
type Language = 'en' | 'es';
type ProficiencyLevel = 'beginner' | 'intermediate' | 'advanced' | 'native';

interface TranslationContext {
  language: Language;
  setLanguage: (lang: Language) => void;
  proficiency: ProficiencyLevel;
  setProficiency: (level: ProficiencyLevel) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  translateWithCulturalContext: (key: string, context?: 'family' | 'school' | 'health' | 'technology') => string;
  isRTL: boolean;
}

// Translation dictionaries
const translations = {
  en: {
    // Common UI
    'welcome': 'Welcome',
    'good_morning': 'Good morning',
    'good_afternoon': 'Good afternoon',
    'good_evening': 'Good evening',
    'hello': 'Hello',
    'goodbye': 'Goodbye',
    'please': 'Please',
    'thank_you': 'Thank you',
    'sorry': 'Sorry',
    'yes': 'Yes',
    'no': 'No',
    'help': 'Help',
    'settings': 'Settings',
    'cancel': 'Cancel',
    'save': 'Save',
    'delete': 'Delete',
    'edit': 'Edit',
    'back': 'Back',
    'next': 'Next',
    'loading': 'Loading...',
    'error': 'Error',
    'success': 'Success',

    // Family Assistant specific
    'family_assistant': 'Family Assistant',
    'talk_to_nexus': 'Talk to Nexus',
    'voice_command': 'Voice Command',
    'family_status': 'Family Status',
    'quick_actions': 'Quick Actions',
    'family_members': 'Family Members',
    'activities': 'Activities',
    'calendar': 'Calendar',
    'homework_help': 'Homework Help',
    'screen_time': 'Screen Time',
    'location': 'Location',
    'parental_controls': 'Parental Controls',

    // Voice commands
    'wake_word': 'Hey Nexus',
    'listening': 'Listening...',
    'voice_command_received': 'Voice Command Received',
    'tap_microphone': 'Tap the microphone or say "{{wake_word}}"',

    // Greetings by role
    'greeting_parent': 'Good morning, {{name}}! Ready to manage the family?',
    'greeting_teenager': 'Good afternoon, {{name}}! What can I help you with today?',
    'greeting_child': 'Good morning, {{name}}! Ready for some fun and learning?',
    'greeting_grandparent': 'Good morning, {{name}}! How can I assist you today?',

    // Time expressions
    'minutes_ago': '{{count}} minutes ago',
    'hours_ago': '{{count}} hours ago',
    'days_ago': '{{count}} days ago',
    'just_now': 'Just now',
    'today': 'Today',
    'tomorrow': 'Tomorrow',
    'yesterday': 'Yesterday',

    // Family roles
    'parent': 'Parent',
    'teenager': 'Teenager',
    'child': 'Child',
    'grandparent': 'Grandparent',

    // Status indicators
    'online': 'Online',
    'offline': 'Offline',
    'busy': 'Busy',
    'at_school': 'At School',
    'at_work': 'At Work',
    'sleeping': 'Sleeping',

    // Educational contexts
    'math_homework': 'Math homework',
    'reading_practice': 'Reading practice',
    'science_project': 'Science project',
    'art_class': 'Art class',
    'music_lesson': 'Music lesson',

    // Family activities
    'family_dinner': 'Family dinner',
    'game_night': 'Game night',
    'movie_time': 'Movie time',
    'bedtime_story': 'Bedtime story',
    'family_call': 'Family video call',
  },

  es: {
    // Common UI
    'welcome': 'Bienvenido',
    'good_morning': 'Buenos días',
    'good_afternoon': 'Buenas tardes',
    'good_evening': 'Buenas noches',
    'hello': 'Hola',
    'goodbye': 'Adiós',
    'please': 'Por favor',
    'thank_you': 'Gracias',
    'sorry': 'Lo siento',
    'yes': 'Sí',
    'no': 'No',
    'help': 'Ayuda',
    'settings': 'Configuración',
    'cancel': 'Cancelar',
    'save': 'Guardar',
    'delete': 'Eliminar',
    'edit': 'Editar',
    'back': 'Atrás',
    'next': 'Siguiente',
    'loading': 'Cargando...',
    'error': 'Error',
    'success': 'Éxito',

    // Family Assistant specific
    'family_assistant': 'Asistente Familiar',
    'talk_to_nexus': 'Hablar con Nexus',
    'voice_command': 'Comando de Voz',
    'family_status': 'Estado Familiar',
    'quick_actions': 'Acciones Rápidas',
    'family_members': 'Miembros de la Familia',
    'activities': 'Actividades',
    'calendar': 'Calendario',
    'homework_help': 'Ayuda con la Tarea',
    'screen_time': 'Tiempo de Pantalla',
    'location': 'Ubicación',
    'parental_controls': 'Controles Parentales',

    // Voice commands
    'wake_word': 'Oye Nexus',
    'listening': 'Escuchando...',
    'voice_command_received': 'Comando de Voz Recibido',
    'tap_microphone': 'Toca el micrófono o di "{{wake_word}}"',

    // Greetings by role
    'greeting_parent': 'Buenos días, {{name}}! ¿Lista para administrar la familia?',
    'greeting_teenager': 'Buenas tardes, {{name}}! ¿En qué puedo ayudarte hoy?',
    'greeting_child': '¡Buenos días, {{name}}! ¿Lista para diversión y aprendizaje?',
    'greeting_grandparent': 'Buenos días, {{name}}! ¿Cómo puedo asistirte hoy?',

    // Time expressions
    'minutes_ago': 'hace {{count}} minutos',
    'hours_ago': 'hace {{count}} horas',
    'days_ago': 'hace {{count}} días',
    'just_now': 'Ahora mismo',
    'today': 'Hoy',
    'tomorrow': 'Mañana',
    'yesterday': 'Ayer',

    // Family roles
    'parent': 'Padre/Madre',
    'teenager': 'Adolescente',
    'child': 'Niño/a',
    'grandparent': 'Abuelo/a',

    // Status indicators
    'online': 'En línea',
    'offline': 'Desconectado',
    'busy': 'Ocupado',
    'at_school': 'En la escuela',
    'at_work': 'En el trabajo',
    'sleeping': 'Durmiendo',

    // Educational contexts
    'math_homework': 'Tarea de matemáticas',
    'reading_practice': 'Práctica de lectura',
    'science_project': 'Proyecto de ciencias',
    'art_class': 'Clase de arte',
    'music_lesson': 'Lección de música',

    // Family activities
    'family_dinner': 'Cena familiar',
    'game_night': 'Noche de juegos',
    'movie_time': 'Hora de película',
    'bedtime_story': 'Cuento para dormir',
    'family_call': 'Videollamada familiar',
  }
};

// Cultural context adaptations
const culturalAdaptations = {
  family: {
    en: {
      'family_dinner': 'Family dinner time',
      'family_gathering': 'Family get-together',
      'respect_elders': 'Respect your elders'
    },
    es: {
      'family_dinner': 'La hora de la cena familiar',
      'family_gathering': 'Reunión familiar',
      'respect_elders': 'Respeta a tus mayores'
    }
  },
  school: {
    en: {
      'homework': 'Homework assignment',
      'parent_teacher_conference': 'Parent-teacher conference',
      'school_bus': 'School bus'
    },
    es: {
      'homework': 'La tarea escolar',
      'parent_teacher_conference': 'Reunión de padres y maestros',
      'school_bus': 'El autobús escolar'
    }
  },
  health: {
    en: {
      'doctor_appointment': "Doctor's appointment",
      'take_medicine': 'Take your medicine',
      'healthy_eating': 'Healthy eating habits'
    },
    es: {
      'doctor_appointment': 'Cita con el doctor',
      'take_medicine': 'Toma tu medicina',
      'healthy_eating': 'Hábitos alimenticios saludables'
    }
  },
  technology: {
    en: {
      'screen_time_limit': 'Screen time limit',
      'digital_safety': 'Digital safety rules',
      'online_privacy': 'Online privacy'
    },
    es: {
      'screen_time_limit': 'Límite de tiempo de pantalla',
      'digital_safety': 'Reglas de seguridad digital',
      'online_privacy': 'Privacidad en línea'
    }
  }
};

const TranslationContext = createContext<TranslationContext | null>(null);

export function useTranslation() {
  const context = useContext(TranslationContext);
  if (!context) {
    throw new Error('useTranslation must be used within BilingualProvider');
  }
  return context;
}

interface BilingualProviderProps {
  children: React.ReactNode;
}

export default function BilingualProvider({ children }: BilingualProviderProps) {
  const { user } = useAuth();
  const [language, setLanguage] = useState<Language>('en');
  const [proficiency, setProficiency] = useState<ProficiencyLevel>('intermediate');

  // Load saved preferences
  useEffect(() => {
    const savedLanguage = localStorage.getItem('preferred-language') as Language;
    const savedProficiency = localStorage.getItem('language-proficiency') as ProficiencyLevel;

    if (savedLanguage) setLanguage(savedLanguage);
    if (savedProficiency) setProficiency(savedProficiency);

    // Auto-detect browser language
    if (!savedLanguage) {
      const browserLang = navigator.language.split('-')[0];
      if (browserLang === 'es') {
        setLanguage('es');
      }
    }

    // Set proficiency based on user role and detected language
    if (user?.role) {
      const roleDefaults = {
        grandparent: language === 'es' ? 'native' : 'beginner',
        parent: language === 'es' ? 'advanced' : 'intermediate',
        teenager: language === 'es' ? 'intermediate' : 'advanced',
        child: language === 'es' ? 'beginner' : 'native'
      };

      if (roleDefaults[user.role as keyof typeof roleDefaults] && !savedProficiency) {
        setProficiency(roleDefaults[user.role as keyof typeof roleDefaults]);
      }
    }
  }, [user?.role, language]);

  // Save preferences
  const handleSetLanguage = (lang: Language) => {
    setLanguage(lang);
    localStorage.setItem('preferred-language', lang);
  };

  const handleSetProficiency = (level: ProficiencyLevel) => {
    setProficiency(level);
    localStorage.setItem('language-proficiency', level);
  };

  // Translation function
  const t = (key: string, params?: Record<string, string | number>): string => {
    const dictionary = translations[language];
    let translation = dictionary[key as keyof typeof dictionary] || key;

    // Replace parameters
    if (params) {
      Object.entries(params).forEach(([param, value]) => {
        translation = translation.replace(`{{${param}}}`, String(value));
      });
    }

    return translation;
  };

  // Cultural context translation
  const translateWithCulturalContext = (key: string, context: keyof typeof culturalAdaptations = 'family'): string => {
    const contextDictionary = culturalAdaptations[context][language];
    return contextDictionary[key as keyof typeof contextDictionary] || t(key);
  };

  // Determine if RTL (currently false for both languages, but prepared for future expansion)
  const isRTL = false;

  const value: TranslationContext = {
    language,
    setLanguage: handleSetLanguage,
    proficiency,
    setProficiency: handleSetProficiency,
    t,
    translateWithCulturalContext,
    isRTL
  };

  return (
    <TranslationContext.Provider value={value}>
      <div lang={language} dir={isRTL ? 'rtl' : 'ltr'}>
        {children}
      </div>
    </TranslationContext.Provider>
  );
}

// Helper components
export function LanguageSelector() {
  const { language, setLanguage, proficiency, setProficiency } = useTranslation();

  return (
    <div className="flex items-center space-x-4">
      {/* Language Toggle */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => setLanguage('en')}
          className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
            language === 'en'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          English
        </button>
        <button
          onClick={() => setLanguage('es')}
          className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
            language === 'es'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Español
        </button>
      </div>

      {/* Proficiency Selector */}
      <select
        value={proficiency}
        onChange={(e) => setProficiency(e.target.value as ProficiencyLevel)}
        className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
      >
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
        <option value="native">Native</option>
      </select>
    </div>
  );
}

// Text-to-speech with language support
export function useBilingualTTS() {
  const { language, proficiency } = useTranslation();

  const speak = (text: string, options?: SpeechSynthesisUtterance) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);

      // Set language
      utterance.lang = language === 'es' ? 'es-ES' : 'en-US';

      // Adjust rate based on proficiency
      const rateAdjustments = {
        beginner: 0.8,
        intermediate: 0.9,
        advanced: 1.0,
        native: 1.0
      };
      utterance.rate = rateAdjustments[proficiency];

      // Apply custom options
      if (options) {
        Object.assign(utterance, options);
      }

      speechSynthesis.speak(utterance);
    }
  };

  return { speak };
}

// Translation helper for dynamic content
export function TranslatedText({
  key,
  params,
  context,
  className
}: {
  key: string;
  params?: Record<string, string | number>;
  context?: keyof typeof culturalAdaptations;
  className?: string;
}) {
  const { t, translateWithCulturalContext } = useTranslation();

  const text = context ? translateWithCulturalContext(key, context) : t(key, params);

  return <span className={className}>{text}</span>;
}