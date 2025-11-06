use ratatui::{
    style::Color,
};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Theme {
    Default,
    Dracula,
    GruvboxDark,
    Nord,
    SolarizedDark,
    Cyberpunk,
    Monokai,
    OneDark,
    TokyoNight,
}

impl Theme {
    pub const ALL: [Theme; 9] = [
        Theme::Default,
        Theme::Dracula,
        Theme::GruvboxDark,
        Theme::Nord,
        Theme::SolarizedDark,
        Theme::Cyberpunk,
        Theme::Monokai,
        Theme::OneDark,
        Theme::TokyoNight,
    ];

    pub fn name(self) -> &'static str {
        match self {
            Theme::Default => "Default",
            Theme::Dracula => "Dracula",
            Theme::GruvboxDark => "Gruvbox Dark",
            Theme::Nord => "Nord",
            Theme::SolarizedDark => "Solarized Dark",
            Theme::Cyberpunk => "Cyberpunk",
            Theme::Monokai => "Monokai",
            Theme::OneDark => "One Dark",
            Theme::TokyoNight => "Tokyo Night",
        }
    }

    pub fn next(self) -> Self {
        let current = Self::ALL.iter().position(|&t| t == self).unwrap_or(0);
        Self::ALL[(current + 1) % Self::ALL.len()]
    }

    pub fn previous(self) -> Self {
        let current = Self::ALL.iter().position(|&t| t == self).unwrap_or(0);
        Self::ALL[(current + Self::ALL.len() - 1) % Self::ALL.len()]
    }
}

#[derive(Debug, Clone)]
pub struct ThemeColors {
    pub primary: Color,
    pub secondary: Color,
    pub success: Color,
    pub warning: Color,
    pub error: Color,
    pub info: Color,
    pub background: Color,
    pub foreground: Color,
    pub text_muted: Color,
    pub highlight: Color,
    pub border: Color,
    pub gauge_good: Color,
    pub gauge_warning: Color,
    pub gauge_danger: Color,
}

impl ThemeColors {
    pub fn from_theme(theme: Theme) -> Self {
        match theme {
            Theme::Default => Self::default(),
            Theme::Dracula => Self::dracula(),
            Theme::GruvboxDark => Self::gruvbox_dark(),
            Theme::Nord => Self::nord(),
            Theme::SolarizedDark => Self::solarized_dark(),
            Theme::Cyberpunk => Self::cyberpunk(),
            Theme::Monokai => Self::monokai(),
            Theme::OneDark => Self::one_dark(),
            Theme::TokyoNight => Self::tokyo_night(),
        }
    }

    fn default() -> Self {
        Self {
            primary: Color::Cyan,
            secondary: Color::Blue,
            success: Color::Green,
            warning: Color::Yellow,
            error: Color::Red,
            info: Color::Magenta,
            background: Color::Black,
            foreground: Color::White,
            text_muted: Color::Gray,
            highlight: Color::Blue,
            border: Color::Blue,
            gauge_good: Color::Green,
            gauge_warning: Color::Yellow,
            gauge_danger: Color::Red,
        }
    }

    fn dracula() -> Self {
        Self {
            primary: Color::Rgb(189, 147, 249),   // Purple
            secondary: Color::Rgb(139, 233, 253),  // Cyan
            success: Color::Rgb(80, 250, 123),     // Green
            warning: Color::Rgb(241, 250, 140),    // Yellow
            error: Color::Rgb(255, 85, 85),        // Red
            info: Color::Rgb(255, 121, 198),       // Pink
            background: Color::Rgb(40, 42, 54),    // Background
            foreground: Color::Rgb(248, 248, 242), // Foreground
            text_muted: Color::Rgb(98, 114, 164),  // Comment
            highlight: Color::Rgb(68, 71, 90),     // Selection
            border: Color::Rgb(98, 114, 164),      // Comment
            gauge_good: Color::Rgb(80, 250, 123),  // Green
            gauge_warning: Color::Rgb(241, 250, 140), // Yellow
            gauge_danger: Color::Rgb(255, 85, 85),  // Red
        }
    }

    fn gruvbox_dark() -> Self {
        Self {
            primary: Color::Rgb(131, 165, 152),    // Aqua
            secondary: Color::Rgb(251, 241, 199),  // Light Yellow
            success: Color::Rgb(184, 187, 38),     // Green
            warning: Color::Rgb(250, 189, 47),     // Yellow
            error: Color::Rgb(251, 73, 52),        // Red
            info: Color::Rgb(211, 134, 155),       // Light Purple
            background: Color::Rgb(40, 40, 40),    // Hard Black
            foreground: Color::Rgb(235, 219, 178), // Light Hard White
            text_muted: Color::Rgb(146, 131, 116), // Medium Gray
            highlight: Color::Rgb(68, 71, 90),     // Selection
            border: Color::Rgb(60, 56, 54),        // Hard Black
            gauge_good: Color::Rgb(184, 187, 38),  // Green
            gauge_warning: Color::Rgb(250, 189, 47), // Yellow
            gauge_danger: Color::Rgb(251, 73, 52),  // Red
        }
    }

    fn nord() -> Self {
        Self {
            primary: Color::Rgb(136, 192, 208),    // Cyan
            secondary: Color::Rgb(129, 161, 193),  // Blue
            success: Color::Rgb(163, 190, 140),    // Green
            warning: Color::Rgb(235, 203, 139),    // Yellow
            error: Color::Rgb(191, 97, 106),      // Red
            info: Color::Rgb(180, 142, 173),       // Purple
            background: Color::Rgb(46, 52, 64),    // Dark Gray
            foreground: Color::Rgb(216, 222, 233), // Light Gray
            text_muted: Color::Rgb(76, 86, 106),   // Medium Gray
            highlight: Color::Rgb(59, 66, 82),     // Highlight
            border: Color::Rgb(67, 76, 94),       // Border
            gauge_good: Color::Rgb(163, 190, 140), // Green
            gauge_warning: Color::Rgb(235, 203, 139), // Yellow
            gauge_danger: Color::Rgb(191, 97, 106), // Red
        }
    }

    fn solarized_dark() -> Self {
        Self {
            primary: Color::Rgb(38, 139, 210),     // Blue
            secondary: Color::Rgb(42, 161, 152),    // Cyan
            success: Color::Rgb(133, 153, 0),      // Green
            warning: Color::Rgb(181, 137, 0),      // Yellow
            error: Color::Rgb(220, 50, 47),        // Red
            info: Color::Rgb(211, 54, 130),        // Magenta
            background: Color::Rgb(0, 43, 54),      // Base03
            foreground: Color::Rgb(131, 148, 150),  // Base0
            text_muted: Color::Rgb(88, 110, 117),   // Base01
            highlight: Color::Rgb(7, 54, 66),       // Base02
            border: Color::Rgb(7, 54, 66),          // Base02
            gauge_good: Color::Rgb(133, 153, 0),    // Green
            gauge_warning: Color::Rgb(181, 137, 0), // Yellow
            gauge_danger: Color::Rgb(220, 50, 47),  // Red
        }
    }

    fn cyberpunk() -> Self {
        Self {
            primary: Color::Rgb(0, 255, 255),       // Cyan
            secondary: Color::Rgb(255, 0, 255),      // Magenta
            success: Color::Rgb(0, 255, 127),       // Spring Green
            warning: Color::Rgb(255, 255, 0),       // Yellow
            error: Color::Rgb(255, 0, 71),          // Red
            info: Color::Rgb(127, 0, 255),          // Purple
            background: Color::Rgb(0, 0, 0),        // Black
            foreground: Color::Rgb(0, 255, 255),    // Cyan
            text_muted: Color::Rgb(127, 127, 127),  // Gray
            highlight: Color::Rgb(255, 255, 255),   // White
            border: Color::Rgb(0, 255, 255),        // Cyan
            gauge_good: Color::Rgb(0, 255, 127),    // Spring Green
            gauge_warning: Color::Rgb(255, 255, 0), // Yellow
            gauge_danger: Color::Rgb(255, 0, 71),   // Red
        }
    }

    fn monokai() -> Self {
        Self {
            primary: Color::Rgb(102, 217, 239),    // Cyan
            secondary: Color::Rgb(249, 38, 114),     // Pink
            success: Color::Rgb(166, 226, 46),      // Green
            warning: Color::Rgb(255, 255, 0),       // Yellow
            error: Color::Rgb(249, 38, 114),        // Pink
            info: Color::Rgb(174, 129, 255),       // Purple
            background: Color::Rgb(39, 40, 34),     // Background
            foreground: Color::Rgb(248, 248, 242),  // Foreground
            text_muted: Color::Rgb(117, 113, 110),  // Gray
            highlight: Color::Rgb(73, 72, 62),      // Selection
            border: Color::Rgb(73, 72, 62),        // Selection
            gauge_good: Color::Rgb(166, 226, 46),   // Green
            gauge_warning: Color::Rgb(255, 255, 0), // Yellow
            gauge_danger: Color::Rgb(249, 38, 114), // Pink
        }
    }

    fn one_dark() -> Self {
        Self {
            primary: Color::Rgb(97, 175, 239),      // Blue
            secondary: Color::Rgb(198, 120, 221),    // Purple
            success: Color::Rgb(152, 195, 121),     // Green
            warning: Color::Rgb(229, 192, 123),     // Yellow
            error: Color::Rgb(224, 108, 117),       // Red
            info: Color::Rgb(226, 140, 145),        // Pink
            background: Color::Rgb(40, 44, 52),     // Background
            foreground: Color::Rgb(171, 178, 191),  // Foreground
            text_muted: Color::Rgb(92, 99, 112),    // Gray
            highlight: Color::Rgb(61, 66, 77),      // Highlight
            border: Color::Rgb(61, 66, 77),        // Highlight
            gauge_good: Color::Rgb(152, 195, 121),  // Green
            gauge_warning: Color::Rgb(229, 192, 123), // Yellow
            gauge_danger: Color::Rgb(224, 108, 117), // Red
        }
    }

    fn tokyo_night() -> Self {
        Self {
            primary: Color::Rgb(125, 179, 255),     // Blue
            secondary: Color::Rgb(187, 154, 247),    // Purple
            success: Color::Rgb(146, 234, 170),     // Green
            warning: Color::Rgb(250, 179, 135),     // Orange
            error: Color::Rgb(242, 139, 130),       // Red
            info: Color::Rgb(250, 208, 196),        // Pink
            background: Color::Rgb(26, 27, 38),     // Background
            foreground: Color::Rgb(169, 177, 214),  // Foreground
            text_muted: Color::Rgb(76, 86, 106),    // Gray
            highlight: Color::Rgb(38, 40, 55),      // Highlight
            border: Color::Rgb(38, 40, 55),         // Highlight
            gauge_good: Color::Rgb(146, 234, 170),  // Green
            gauge_warning: Color::Rgb(250, 179, 135), // Orange
            gauge_danger: Color::Rgb(242, 139, 130), // Red
        }
    }
}