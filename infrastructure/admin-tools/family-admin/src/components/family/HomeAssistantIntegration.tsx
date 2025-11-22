"use client";

import React, { useState, useEffect } from "react";

interface HomeAssistantConfig {
  enabled: boolean;
  url: string;
  accessToken?: string;
  entities: {
    light_switches: string[];
    smart_speakers: string[];
    displays: string[];
    sensors: string[];
  };
  voice_commands: {
    wake_word: string;
    confidence_threshold: number;
    custom_commands: VoiceCommand[];
  };
}

interface VoiceCommand {
  id: string;
  phrase: string;
  intent: string;
  entities: Record<string, any>;
  response_template?: string;
  ha_service?: string;
}

export default function HomeAssistantIntegration() {
  const [config, setConfig] = useState<HomeAssistantConfig>({
    enabled: false,
    url: "",
    entities: {
      light_switches: [],
      smart_speakers: [],
      displays: [],
      sensors: []
    },
    voice_commands: {
      wake_word: "Hey Nexus",
      confidence_threshold: 0.7,
      custom_commands: []
    }
  });

  const [isConnected, setIsConnected] = useState(false);
  const [haStatus, setHaStatus] = useState<any>(null);
  const [testingCommand, setTestingCommand] = useState("");

  // Custom voice commands for Home Assistant
  const defaultCommands: VoiceCommand[] = [
    {
      id: "lights_on",
      phrase: "turn on the lights",
      intent: "HassLightSet",
      entities: { brightness: 255, color_name: "white" },
      ha_service: "light.turn_on"
    },
    {
      id: "lights_off",
      phrase: "turn off the lights",
      intent: "HassLightSet",
      entities: {},
      ha_service: "light.turn_off"
    },
    {
      id: "morning_routine",
      phrase: "good morning nexus",
      intent: "MorningRoutine",
      entities: {},
      response_template: "Good morning! I'm turning on the lights, checking your calendar, and starting the coffee maker."
    },
    {
      id: "bedtime_routine",
      phrase: "good night nexus",
      intent: "BedtimeRoutine",
      entities: {},
      response_template: "Good night! I'm dimming the lights, setting the alarm, and activating security mode."
    },
    {
      id: "family_announcement",
      phrase: "announce to the family",
      intent: "FamilyAnnouncement",
      entities: { message: "" },
      ha_service: "tts.speak"
    },
    {
      id: "where_is_family",
      phrase: "where is everyone",
      intent: "FamilyLocationQuery",
      entities: {},
      response_template: "Sarah is at work, Alex is at school, Emma is at school, and Robert is at home."
    },
    {
      id: "dinner_ready",
      phrase: "dinner is ready",
      intent: "DinnerAnnouncement",
      entities: {},
      response_template: "Dinner announcement sent to all family devices!",
      ha_service: "notify.notify"
    },
    {
      id: "movie_time",
      phrase: "it's movie time",
      intent: "MovieMode",
      entities: {},
      response_template: "Movie mode activated! Lights dimming, TV turning on, and sound system ready.",
      ha_service: "script.movie_mode"
    },
    {
      id: "homework_mode",
      phrase: "homework mode",
      intent: "HomeworkMode",
      entities: {},
      response_template: "Homework mode activated! Study lights on, distractions paused.",
      ha_service: "script.homework_mode"
    },
    {
      id: "emergency_alert",
      phrase: "emergency nexus",
      intent: "EmergencyAlert",
      entities: {},
      response_template: "Emergency alert sent to all family members and emergency contacts!",
      ha_service: "script.emergency_alert"
    }
  ];

  useEffect(() => {
    // Load saved config from localStorage
    const savedConfig = localStorage.getItem('ha-config');
    if (savedConfig) {
      setConfig({
        ...JSON.parse(savedConfig),
        voice_commands: {
          ...JSON.parse(savedConfig).voice_commands,
          custom_commands: defaultCommands
        }
      });
    } else {
      setConfig(prev => ({
        ...prev,
        voice_commands: {
          ...prev.voice_commands,
          custom_commands: defaultCommands
        }
      }));
    }
  }, []);

  // Test Home Assistant connection
  const testConnection = async () => {
    if (!config.url || !config.accessToken) {
      alert('Please enter Home Assistant URL and Access Token first');
      return;
    }

    try {
      const response = await fetch(`${config.url}/api/`, {
        headers: {
          'Authorization': `Bearer ${config.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setHaStatus(data);
        setIsConnected(true);
        alert('Connected to Home Assistant successfully!');
      } else {
        setIsConnected(false);
        alert('Failed to connect to Home Assistant. Check your URL and token.');
      }
    } catch (error) {
      setIsConnected(false);
      alert('Error connecting to Home Assistant: ' + error.message);
    }
  };

  // Test voice command
  const testVoiceCommand = async (command: VoiceCommand) => {
    if (!isConnected) {
      alert('Please connect to Home Assistant first');
      return;
    }

    try {
      // Mock command execution - replace with actual HA API call
      console.log('Executing command:', command);
      alert(`Command "${command.phrase}" would execute ${command.ha_service || command.intent}`);
    } catch (error) {
      alert('Error executing command: ' + error.message);
    }
  };

  // Save configuration
  const saveConfig = () => {
    localStorage.setItem('ha-config', JSON.stringify(config));
    alert('Configuration saved!');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Home Assistant Integration
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Connect Nexus with your smart home for voice-controlled automation
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            isConnected
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              : "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400"
          }`}>
            {isConnected ? "Connected" : "Not Connected"}
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Configuration
        </h3>

        <div className="space-y-4">
          {/* Enable/Disable */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Enable Home Assistant Integration
            </label>
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => setConfig(prev => ({ ...prev, enabled: e.target.checked }))}
              className="rounded text-blue-600"
            />
          </div>

          {/* Home Assistant URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Home Assistant URL
            </label>
            <input
              type="url"
              value={config.url}
              onChange={(e) => setConfig(prev => ({ ...prev, url: e.target.value }))}
              placeholder="https://your-home-assistant.local:8123"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          {/* Access Token */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Long-Lived Access Token
            </label>
            <input
              type="password"
              value={config.accessToken || ""}
              onChange={(e) => setConfig(prev => ({ ...prev, accessToken: e.target.value }))}
              placeholder="Your Home Assistant access token"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Create a token in Home Assistant: Profile > Long-Lived Access Tokens
            </p>
          </div>

          {/* Test Connection */}
          <div className="flex space-x-3">
            <button
              onClick={testConnection}
              disabled={!config.url || !config.accessToken}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Test Connection
            </button>
            <button
              onClick={saveConfig}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Save Configuration
            </button>
          </div>
        </div>
      </div>

      {/* Voice Commands */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Voice Commands
        </h3>

        <div className="space-y-4">
          {/* Wake Word */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Wake Word
            </label>
            <input
              type="text"
              value={config.voice_commands.wake_word}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                voice_commands: { ...prev.voice_commands, wake_word: e.target.value }
              }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          {/* Custom Commands */}
          <div>
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
              Pre-configured Commands
            </h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {config.voice_commands.custom_commands.map((command) => (
                <div
                  key={command.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 dark:text-white">
                      "{command.phrase}"
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Intent: {command.intent}
                      {command.ha_service && ` • Service: ${command.ha_service}`}
                    </p>
                    {command.response_template && (
                      <p className="text-sm text-gray-500 dark:text-gray-500 italic">
                        "{command.response_template}"
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => testVoiceCommand(command)}
                    disabled={!isConnected}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    Test
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Test Custom Command */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Test Custom Command
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={testingCommand}
                onChange={(e) => setTestingCommand(e.target.value)}
                placeholder="Type a command to test..."
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <button
                onClick={() => {
                  // Find matching command
                  const match = config.voice_commands.custom_commands.find(cmd =>
                    cmd.phrase.toLowerCase().includes(testingCommand.toLowerCase()) ||
                    testingCommand.toLowerCase().includes(cmd.phrase.toLowerCase())
                  );
                  if (match) {
                    testVoiceCommand(match);
                  } else {
                    alert('No matching command found');
                  }
                }}
                disabled={!isConnected || !testingCommand}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Test
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Device Setup */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Smart Device Setup
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Smart Speakers */}
          <div>
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
              Smart Speakers & Displays
            </h4>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <p>• Amazon Echo devices</p>
              <p>• Google Nest devices</p>
              <p>• Apple HomePod</p>
              <p>• Custom Raspberry Pi displays</p>
              <p>• Tablet wall mounts</p>
            </div>
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                💡 Smart speakers will listen for the wake word and process commands through Home Assistant's voice pipeline.
              </p>
            </div>
          </div>

          {/* Sensors & Inputs */}
          <div>
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
              Sensors & Inputs
            </h4>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <p>• Motion sensors</p>
              <p>• Door/window sensors</p>
              <p>• Smart buttons</p>
              <p>• Presence detection</p>
              <p>• Family member tracking</p>
            </div>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-green-800 dark:text-green-200">
                💡 Sensors provide context for proactive assistance and automated routines.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Example Routines */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Example Family Routines
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Morning Routine */}
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
              🌅 Morning Routine
            </h4>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-3">
              Trigger: "Good morning Nexus"
            </p>
            <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
              <li>• Turn on bedroom lights (30% brightness)</li>
              <li>• Start coffee maker</li>
              <li>• Announce today's schedule</li>
              <li>• Check weather and traffic</li>
              <li>• Play morning playlist</li>
            </ul>
          </div>

          {/* School Routine */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
              🎒 School Routine
            </h4>
            <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
              Trigger: 7:30 AM weekdays
            </p>
            <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
              <li>• Announce school departure reminder</li>
              <li>• Check backpack contents</li>
              <li>• Verify homework completion</li>
              <li>• Provide lunch checklist</li>
              <li>• Lock doors when everyone leaves</li>
            </ul>
          </div>

          {/* Dinner Routine */}
          <div className="p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
            <h4 className="font-semibold text-orange-800 dark:text-orange-200 mb-2">
              🍽️ Dinner Routine
            </h4>
            <p className="text-sm text-orange-700 dark:text-orange-300 mb-3">
              Trigger: "Dinner's ready" or 6:00 PM
            </p>
            <ul className="text-sm text-orange-700 dark:text-orange-300 space-y-1">
              <li>• Announce dinner to all devices</li>
              <li>• Pause TVs and tablets</li>
              <li>• Set dining room lighting</li>
              <li>• Play dinner music</li>
              <li>• Take family photo</li>
            </ul>
          </div>

          {/* Bedtime Routine */}
          <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg">
            <h4 className="font-semibold text-indigo-800 dark:text-indigo-200 mb-2">
              🌙 Bedtime Routine
            </h4>
            <p className="text-sm text-indigo-700 dark:text-indigo-300 mb-3">
              Trigger: "Good night Nexus"
            </p>
            <ul className="text-sm text-indigo-700 dark:text-indigo-300 space-y-1">
              <li>• Dim lights throughout house</li>
              <li>• Lock doors and arm security</li>
              <li>• Set morning alarms</li>
              <li>• Start bedtime music/stories</li>
              <li>• Enable "Do Not Disturb"</li>
            </ul>
          </div>

          {/* Movie Mode */}
          <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
            <h4 className="font-semibold text-purple-800 dark:text-purple-200 mb-2">
              🎬 Movie Mode
            </h4>
            <p className="text-sm text-purple-700 dark:text-purple-300 mb-3">
              Trigger: "It's movie time"
            </p>
            <ul className="text-sm text-purple-700 dark:text-purple-300 space-y-1">
              <li>• Dim living room lights</li>
              <li>• Turn on TV and sound system</li>
              <li>• Close smart blinds</li>
              <li>• Set phone to silent mode</li>
              <li>• Start popcorn maker</li>
            </ul>
          </div>

          {/* Emergency Alert */}
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <h4 className="font-semibold text-red-800 dark:text-red-200 mb-2">
              🚨 Emergency Alert
            </h4>
            <p className="text-sm text-red-700 dark:text-red-300 mb-3">
              Trigger: "Emergency Nexus"
            </p>
            <ul className="text-sm text-red-700 dark:text-red-300 space-y-1">
              <li>• Alert all family members</li>
              <li>• Call emergency contacts</li>
              <li>• Turn on all lights</li>
              <li>• Start security recording</li>
              <li>• Unlock doors for responders</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Installation Guide */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Installation Guide
        </h3>

        <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
          <div>
            <h4 className="font-semibold mb-2">1. Enable Home Assistant Integration</h4>
            <p>Install the "Nexus Family Assistant" integration from HACS or manually add the custom component.</p>
          </div>

          <div>
            <h4 className="font-semibold mb-2">2. Configure Voice Assistant</h4>
            <p>Set up a voice pipeline (like Whisper + Piper) and create intent sentences for family commands.</p>
          </div>

          <div>
            <h4 className="font-semibold mb-2">3. Add Smart Devices</h4>
            <p>Add your smart speakers, displays, and sensors to Home Assistant with proper entity IDs.</p>
          </div>

          <div>
            <h4 className="font-semibold mb-2">4. Create Automations</h4>
            <p>Set up automations that trigger based on voice commands, time, or sensor states.</p>
          </div>

          <div>
            <h4 className="font-semibold mb-2">5. Test Everything</h4>
            <p>Test voice commands on different devices and ensure proper responses and actions.</p>
          </div>
        </div>

        <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <p className="text-sm text-green-800 dark:text-green-200">
            <strong>Pro Tip:</strong> Start with a few basic commands and gradually expand your automation library based on your family's daily routines.
          </p>
        </div>
      </div>
    </div>
  );
}