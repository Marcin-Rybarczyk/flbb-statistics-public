# User Features Guide

This guide covers the personalization and user experience features available in the FLBB Statistics application.

## 🎨 Themes

The application supports 6 beautiful themes to customize your viewing experience:

### Available Themes

1. **Default** - Clean and professional light theme
2. **Ocean** - Cool blue tones inspired by ocean depths
3. **Sunset** - Warm oranges and reds for a vibrant look
4. **Forest** - Natural green tones for a calming experience
5. **Minimal** - Ultra-clean minimalist design
6. **Cherry** - Bold pinks and reds for a striking appearance

### How to Change Themes

1. Navigate to the **Preferences** page (`/preferences`)
2. Select your preferred theme from the dropdown menu
3. Click **Save Preferences**
4. Your theme choice is saved in your browser session

### Theme Persistence

- Theme preferences are stored in your browser session
- Your selection persists across page visits during your session
- Preferences are maintained until you close your browser or clear cookies

## ⚙️ User Preferences

Access the Preferences page to customize your experience:

### Available Preferences

#### 1. Preferred Division
- Set your default division to see relevant standings first
- Options include all available divisions (Division 1-4, Enovos League, etc.)
- When set, the home page automatically filters to your preferred division

#### 2. Preferred Team
- Choose your favorite team to see their stats highlighted
- Team-specific shortcuts and quick access to team details
- Personalized dashboard showing your team's upcoming games

#### 3. Theme Selection
- Choose from 6 custom themes (see Themes section above)
- Live preview of theme changes
- Instant application across all pages

### Accessing Preferences

**From the navigation:**
1. Click on **Preferences** in the main navigation menu
2. Or visit `/preferences` directly

**What you can customize:**
```
┌─────────────────────────────────────┐
│         User Preferences            │
├─────────────────────────────────────┤
│ Preferred Division: [Dropdown]      │
│ Preferred Team:     [Dropdown]      │
│ Theme:              [Dropdown]      │
│                                     │
│         [Save Preferences]          │
└─────────────────────────────────────┘
```

### How Preferences Work

**Session Storage:**
- Preferences are stored in Flask sessions
- Secured with Flask's session management
- Automatically loaded on each page visit

**Preference Impact:**
- **Division:** Filters home page standings automatically
- **Team:** Highlights team in listings, quick access to team details
- **Theme:** Changes color scheme and styling across all pages

## 🔔 Session Information

### What is Stored

The application stores the following in your session:
- `preferred_division` - Your chosen division
- `preferred_team` - Your favorite team
- `preferred_theme` - Your selected theme

### Privacy

- All preferences are stored locally in your browser
- No personal information is collected or stored
- Preferences are session-based and cleared when you close your browser
- No tracking or analytics on user preferences

## 📱 Responsive Design

The application is optimized for all devices:

### Desktop Experience
- Full navigation with all features
- Large data tables with sorting and filtering
- Interactive charts and visualizations
- Sidebar navigation for quick access

### Tablet Experience
- Optimized layout for medium screens
- Collapsible navigation menu
- Touch-friendly interface
- Responsive tables that adapt to screen width

### Mobile Experience
- Mobile-first design approach
- Simplified navigation with hamburger menu
- Swipeable tables and scrollable content
- Touch-optimized buttons and controls

## 💡 Pro Tips

### Quick Navigation
1. **Set your preferences first** - Choose your favorite team and division for a personalized experience
2. **Use hover tooltips** - Hover over player/team names for quick stats (desktop only)
3. **Bookmark specific pages** - Bookmark your team's detail page for quick access
4. **Try different themes** - Experiment with themes to find your favorite

### Best Practices
- **Keep preferences updated** - Update your preferred team if you switch allegiance
- **Use filters** - Combine preferences with page-specific filters for targeted data
- **Explore all pages** - Don't miss the advanced analytics on the "Deeper Analysis" page
- **Check admin page** - Visit the admin page to import historical season data

### Keyboard Shortcuts
While the application doesn't currently have keyboard shortcuts, you can use standard browser shortcuts:
- `Ctrl+F` / `Cmd+F` - Search for text on current page
- `Ctrl+R` / `Cmd+R` - Refresh data
- Browser back/forward buttons - Navigate between pages

## 🎯 Feature Roadmap

### Coming Soon
- [ ] Email notifications for game results
- [ ] Custom dashboard widgets
- [ ] Dark mode (in addition to existing themes)
- [ ] Favorite players list
- [ ] Game reminders
- [ ] Social sharing features

### Under Consideration
- [ ] Account system for cloud-saved preferences
- [ ] Multi-team following
- [ ] Custom color schemes
- [ ] Accessibility improvements
- [ ] Keyboard navigation shortcuts

## 📞 Support

If you have questions about user features:
1. Check this documentation first
2. Review the [main README](../README.md) for general information
3. Open an issue on GitHub for feature requests
4. Report bugs through the issue tracker

---

**Enjoy your personalized basketball statistics experience!** 🏀
