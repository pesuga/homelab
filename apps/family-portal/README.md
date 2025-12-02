# Family Assistant App

A family-friendly AI assistant interface that adapts to different family members' needs and preferences.

## 🏠 Features

### Adaptive User Interface
- **Role-based layouts**: Different interfaces for parents, teenagers, children, and grandparents
- **Age-appropriate content**: Complexity and features adjust based on user age and role
- **Responsive design**: Works seamlessly on mobile, tablet, and desktop devices
- **Accessibility first**: WCAG 2.1 AA compliance with large text and high contrast options

### Voice-First Interaction
- **Natural conversation**: Talk to the assistant using everyday language
- **Visual feedback**: See what the assistant hears in real-time
- **Contextual responses**: Role-appropriate personality and communication style
- **Multi-language support**: English and Spanish with cultural context

### Family Coordination
- **Real-time status**: See what family members are doing
- **Shared calendar**: Family schedule and events
- **Homework help**: AI-powered assistance for schoolwork
- **Reminders**: Set and manage family reminders

### Progressive Web App
- **Offline capable**: Core features work without internet
- **Installable**: Add to home screen like a native app
- **Push notifications**: Important family alerts and reminders
- **Cross-platform**: Works on iOS, Android, and desktop

## 🚀 Getting Started

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd family-assistant/family-app
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The built app will be in the `dist` directory.

## 🎨 Design System

### Color Palettes

#### Family-Friendly Base Colors
- **Primary Orange**: `#f29224` - Warm, inviting, energetic
- **Neutral Grays**: `#78716c` - Professional, calm
- **Success Green**: `#22c55e` - Positive feedback
- **Warning Yellow**: `#f59e0b` - Gentle alerts

#### Role-Specific Accents
- **Parent Purple**: `#9b59b6` - Wisdom, authority
- **Teen Blue**: `#3498db` - Energy, modern
- **Child Yellow**: `#f1c40f` - Fun, creativity
- **Grandparent Teal**: `#16a085` - Calm, stability

### Typography
- **Primary Font**: Inter (clean, readable)
- **Display Font**: Fredoka One (playful for children)
- **Adaptive Sizing**: Text scales based on user age and preferences

### Layout Density
- **Spacious**: Children and grandparents (larger touch targets)
- **Comfortable**: Parents (balanced layout)
- **Compact**: Teenagers (information-dense)

## 👥 User Roles

### Parent View
- Family overview and management
- Scheduling and coordination
- Privacy controls and monitoring
- Homework progress tracking

### Teenager View
- Personal schedule and tasks
- Homework help and learning
- Social features and entertainment
- Privacy-respecting autonomy

### Child View
- Fun and educational content
- Simple, colorful interface
- Voice-first interaction
- Safe, age-appropriate features

### Grandparent View
- Large text and clear navigation
- Family connection features
- Simple voice commands
- Health and medication reminders

## 🔧 Configuration

### User Profiles

Each family member has a profile with:

```typescript
interface FamilyMember {
  id: string;
  name: string;
  role: 'parent' | 'teenager' | 'child' | 'grandparent';
  age: number;
  preferences: {
    language: 'en' | 'es';
    voiceGender: 'male' | 'female' | 'neutral';
    theme: 'light' | 'dark' | 'auto';
    textSize: 'small' | 'medium' | 'large' | 'extra-large';
  };
}
```

### Adaptive Configuration

The interface automatically adapts based on:

- **Time of day**: Different greetings and suggestions
- **User role**: Appropriate features and complexity
- **Age group**: Text size and interaction patterns
- **Preferences**: Language, theme, and accessibility settings

## 🎯 Voice Commands

### General Commands
- "What's on the family schedule today?"
- "Help me with my homework"
- "Set a reminder for [task]"
- "Tell me a story"
- "Where's [family member]?"

### Role-Specific Commands

#### Parents
- "Are the kids home from school?"
- "What's Emma's screen time today?"
- "Add milk to the shopping list"

#### Teenagers
- "What's my homework for tomorrow?"
- "Set up a study session"
- "What time is practice?"

#### Children
- "Read me a story"
- "Help me with math"
- "Play a game"

#### Grandparents
- "Show me family photos"
- "Call Sarah"
- "What are the grandkids doing?"

## 🔒 Privacy & Safety

### Child Safety
- Content filtering and age-appropriate responses
- Screen time controls
- Safe search and web filtering
- Location sharing with boundaries

### Data Privacy
- Local-first data storage (homelab infrastructure)
- End-to-end encryption for sensitive information
- Family-managed consent and permissions
- Minimal data collection

### Accessibility
- WCAG 2.1 AA compliance
- Screen reader support
- Keyboard navigation
- High contrast and large text options
- Voice control for all functions

## 🌐 Multi-Platform Support

### Mobile/Web (Primary)
- Progressive Web App (PWA)
- Responsive design for all screen sizes
- Touch-optimized interactions
- Offline capabilities

### Smart Home Integration
- Home Assistant voice skills
- Smart display optimization
- Multi-room audio coordination
- Family-wide announcements

### Messaging Platforms
- Telegram integration with rich media
- WhatsApp support (where available)
- Cross-platform conversation sync
- Media sharing and processing

## 🚀 Deployment

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run preview
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist ./dist
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Test all changes with different user roles
3. Ensure accessibility compliance
4. Update documentation for new features

## 📄 License

[License information]

## 🆘 Support

For support and questions:
- Check the documentation
- Review the troubleshooting guide
- Contact the family administrator

---

Built with ❤️ for modern families.