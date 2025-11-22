"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";

interface VoiceInterfaceProps {
  onVoiceCommand?: (command: string, transcript: string) => void;
  wakeWord?: string;
  assistantName?: string;
}

interface AudioVisualizerProps {
  isListening: boolean;
  audioLevel?: number;
}

export default function VoiceInterface({
  onVoiceCommand,
  wakeWord = "Hey Nexus",
  assistantName = "Nexus"
}: VoiceInterfaceProps) {
  const { user } = useAuth();
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [confidence, setConfidence] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [wakeWordDetected, setWakeWordDetected] = useState(false);
  const [isContinuous, setIsContinuous] = useState(false);

  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();

      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => {
        setIsListening(true);
        setTranscript("");
        setConfidence(0);
      };

      recognitionRef.current.onresult = (event: any) => {
        let finalTranscript = "";
        let interimTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
            setConfidence(event.results[i][0].confidence);
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(finalTranscript || interimTranscript);

        // Check for wake word in continuous mode
        if (isContinuous && interimTranscript.toLowerCase().includes(wakeWord.toLowerCase())) {
          setWakeWordDetected(true);
          setTimeout(() => setWakeWordDetected(false), 3000);
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setIsProcessing(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        setIsProcessing(false);

        if (transcript && onVoiceCommand) {
          onVoiceCommand(transcript, transcript);
        }
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [onVoiceCommand, wakeWord, isContinuous, transcript]);

  // Audio visualization setup
  const setupAudioVisualization = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;

      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);

      updateAudioLevel();
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const updateAudioLevel = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
    setAudioLevel(average / 255); // Normalize to 0-1

    animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setIsProcessing(true);
      recognitionRef.current.start();
      setupAudioVisualization();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      setIsProcessing(false);
      setAudioLevel(0);
    }
  };

  const toggleContinuousMode = () => {
    setIsContinuous(!isContinuous);
    if (!isContinuous && recognitionRef.current) {
      recognitionRef.current.continuous = true;
    } else if (recognitionRef.current) {
      recognitionRef.current.continuous = false;
    }
  };

  // Voice response simulation
  const speakResponse = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = user?.role === 'child' ? 1.2 : user?.role === 'grandparent' ? 0.8 : 1.0;
      speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center">
            <span className="mr-3">🎤</span>
            {assistantName} Voice Assistant
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Say "{wakeWord}" or tap the microphone
          </p>
        </div>

        {/* Continuous Mode Toggle */}
        <button
          onClick={toggleContinuousMode}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            isContinuous
              ? 'bg-green-500 text-white hover:bg-green-600'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300'
          }`}
        >
          {isContinuous ? 'Continuous On' : 'Continuous Off'}
        </button>
      </div>

      {/* Wake Word Detection Alert */}
      {wakeWordDetected && (
        <div className="mb-4 p-4 bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <p className="text-green-800 dark:text-green-200 font-medium">
              Wake word detected! {assistantName} is listening...
            </p>
          </div>
        </div>
      )}

      {/* Voice Visualization */}
      <div className="flex flex-col items-center space-y-6">
        {/* Microphone Button with Visualization */}
        <div className="relative">
          {isListening ? (
            <div className="relative">
              {/* Pulsing circles */}
              <div className="absolute inset-0 w-32 h-32 bg-red-500 rounded-full animate-ping opacity-20"></div>
              <div className="absolute inset-0 w-32 h-32 bg-red-500 rounded-full animate-ping opacity-20 animation-delay-200"></div>
              <div className="absolute inset-0 w-32 h-32 bg-red-500 rounded-full animate-ping opacity-20 animation-delay-400"></div>

              {/* Main button */}
              <button
                onClick={stopListening}
                className="relative w-32 h-32 bg-gradient-to-br from-red-500 to-red-600 text-white rounded-full flex flex-col items-center justify-center shadow-lg hover:from-red-600 hover:to-red-700 transition-all transform hover:scale-105"
              >
                <svg className="w-12 h-12 mb-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 012 0v4a1 1 0 11-2 0V7zm4 0a1 1 0 112 0v4a1 1 0 11-2 0V7z" clipRule="evenodd" />
                </svg>
                <span className="text-sm font-medium">Listening</span>
              </button>
            </div>
          ) : (
            <button
              onClick={startListening}
              disabled={isProcessing}
              className="w-32 h-32 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-full flex flex-col items-center justify-center shadow-lg hover:from-blue-600 hover:to-blue-700 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <>
                  <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mb-1"></div>
                  <span className="text-sm font-medium">Processing</span>
                </>
              ) : (
                <>
                  <svg className="w-12 h-12 mb-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm font-medium">Tap to Talk</span>
                </>
              )}
            </button>
          )}

          {/* Audio Level Indicator */}
          {isListening && audioLevel > 0 && (
            <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
              <div className="flex space-x-1">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-1 h-4 rounded-full transition-all duration-100 ${
                      audioLevel > i * 0.2 ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                    style={{ height: `${8 + audioLevel * 16}px` }}
                  ></div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Transcript Display */}
        {transcript && (
          <div className="w-full max-w-2xl">
            <div className={`p-4 rounded-lg border-2 ${
              confidence > 0.8
                ? 'bg-green-50 border-green-300 dark:bg-green-900/20 dark:border-green-700'
                : confidence > 0.5
                ? 'bg-yellow-50 border-yellow-300 dark:bg-yellow-900/20 dark:border-yellow-700'
                : 'bg-red-50 border-red-300 dark:bg-red-900/20 dark:border-red-700'
            }`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    You said:
                  </p>
                  <p className="text-lg text-gray-900 dark:text-white">
                    {transcript}
                  </p>
                  {confidence > 0 && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                      Confidence: {Math.round(confidence * 100)}%
                    </p>
                  )}
                </div>

                {/* Confidence indicator */}
                <div className={`w-3 h-3 rounded-full ml-3 ${
                  confidence > 0.8 ? 'bg-green-500' :
                  confidence > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
              </div>
            </div>
          </div>
        )}

        {/* Voice Commands Help */}
        <div className="w-full max-w-2xl">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Example Voice Commands:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-blue-500">•</span>
                <span className="text-gray-600 dark:text-gray-400">"Hey Nexus, what's on the family calendar?"</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-500">•</span>
                <span className="text-gray-600 dark:text-gray-400">"Remind Alex to do homework at 4 PM"</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-500">•</span>
                <span className="text-gray-600 dark:text-gray-400">"Where's Dad right now?"</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-500">•</span>
                <span className="text-gray-600 dark:text-gray-400">"Tell me a story for bedtime"</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-500">•</span>
                <span className="text-gray-600 dark:text-gray-400">"Add milk to the shopping list"</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-500">•</span>
                <span className="text-gray-600 dark:text-gray-400">"Start a family video call"</span>
              </div>
            </div>
          </div>
        </div>

        {/* Role-specific voice tips */}
        {user?.role && (
          <div className="w-full max-w-2xl">
            <div className={`p-4 rounded-lg border ${
              user.role === 'child'
                ? 'bg-pink-50 border-pink-200 dark:bg-pink-900/20 dark:border-pink-800'
                : user.role === 'grandparent'
                ? 'bg-teal-50 border-teal-200 dark:bg-teal-900/20 dark:border-teal-800'
                : 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800'
            }`}>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <span className="font-semibold">
                  {user.role === 'child' && "🎈 Fun Tips:"}
                  {user.role === 'teenager' && "🎯 Quick Tips:"}
                  {user.role === 'parent' && "👨‍👩‍👧‍👦 Family Management:"}
                  {user.role === 'grandparent' && "💙 Helpful Tips:"}
                </span>
                {" "}
                {user.role === 'child' && "Speak clearly and have fun! I can help with homework and tell stories!"}
                {user.role === 'teenager' && "Quick commands work best. Ask for homework help or schedule reminders!"}
                {user.role === 'parent' && "Manage family tasks, set reminders, and check on family members!"}
                {user.role === 'grandparent' && "I can read things aloud, set health reminders, and connect you with family!"}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Separate Audio Visualizer Component for reuse
export function AudioVisualizer({ isListening, audioLevel = 0 }: AudioVisualizerProps) {
  if (!isListening) return null;

  return (
    <div className="flex items-center justify-center space-x-1 h-16">
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-gradient-to-t from-blue-500 to-purple-500 rounded-full transition-all duration-100"
          style={{
            height: `${Math.random() * 64 * audioLevel + 4}px`,
            opacity: audioLevel
          }}
        ></div>
      ))}
    </div>
  );
}