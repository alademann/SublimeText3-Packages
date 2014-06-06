# Predawn

### A dark interface and syntax theme for Sublime Text.

## About

Predawn is a minimal Sublime Text theme and a syntax color scheme. It was originally just a slightly tweaked version (called Flatland-Alt) of the [Flatland](https://github.com/thinkpixellab/flatland) theme, which itself is a flat reworking of [Soda](https://github.com/buymeasoda/soda-theme/). I decided to keep going with cusomization and rework the entire theme. But I owe a lot to Flatland and Soda. Thanks guys!

![image](screenshots/screenshot.png)

[View a larger screenshot](https://raw.github.com/jamiewilson/predawn/master/screenshots/screenshot-large.png)

## Installation

###Recommended
For easy installation, install with [Package Control](https://sublime.wbond.net/docs).

1. `Cmd+Shift+P` (OS X) `Ctrl+Shift+P` (Win/Linux)
2. type `Package Control: Install Package`
3. Search `predawn`

**Other Methods**

You can clone the repo to your `Packages` folder. Just make sure the repo folder is named `Predawn`.

Of course, you can always [install manually](https://github.com/jamiewilson/predawn/archive/master.zip), too.

## Activating the Theme

Open your user settings file `preferences.sublime-settings` as shown below:

![image](screenshots/activate.png)

Add or replace your current theme settings with the code below.

	{
	"theme": "predawn.sublime-theme",
	"color_scheme": "Packages/Predawn/predawn.tmTheme"
	}

## Tab Height Size Options

You can change the height of the file tabs by adding either to your preferences file:


	"tabs_small": true

OR

	"tabs_medium": true


![image](screenshots/tabs.png)

## Sidebar Size Options

You can change the vertical spacing of the sidebar by changing `default` to `xsmall`, `small`, `medium`, `large`, `xlarge`:


	"sidebar_default": true

for example:

	"sidebar_large": true


![image](screenshots/sidebar.png)

## Markdown Settings
![markdown](screenshots/markdown.png)

#### To enable Predawn for Markdown

First, **open a markdown(.md) file**, then navigate to `Sublime Text` > `Preferences` > `Settings - More` > `Syntax Specific - User`  in the menu bar.

![syntax-specific](screenshots/syntax-specific.png)

#### Add to your current settings or replace with the following:

	{
		"color_scheme": "Packages/Predawn/predawn-markdown.tmTheme",
		"draw_centered": true, // Centers the column in the window
		"draw_indent_guides": false,
		"font_size": 15,
		"trim_trailing_white_space_on_save": false,
		"word_wrap": true,
		"wrap_width": 80  // Sets the # of characters per line
	}
	
## Dock Icons
There are also some [dock icons](/icons) for you to choose from:

![image](screenshots/icons.png)


## A few of my favorite options
These are just a few of my other favorite options for Sublime Text:

	// Typography

	"font_face": "Source Code Pro",
	"font_size": 14,
	"font_options": ["no_round"],
	"highlight_line": true,
	"caret_extra_width": 1,
	"caret_style": "phase",
	"word_wrap": false,

	// Whitespace, Matching, Copy & Auto-Complete

	"copy_with_empty_selection": false,
	"drag_text": false,
	"match_brackets_content": false,
	"match_selection": false,
	"match_tags": false,
	"translate_tabs_to_spaces": true,
	"trim_trailing_white_space_on_save": true,

	// Interface & Behavior

	"close_windows_when_empty": false,
	"draw_minimap_border": true,
	"enable_tab_scrolling": false,
	"overlay_scroll_bars": "enabled",
	"open_files_in_new_window": false,
	"preview_on_click": false,
	"scroll_past_end": true,
	"scroll_speed": 5.0,
	"show_full_path": false,

## And some recommendations

Also, I highly recommend these Sublime Text packages:

[Sublime-CSS3](https://github.com/i-akhmadullin/Sublime-CSS3)  
[GitGutter](https://github.com/jisaacks/GitGutter)  
[Sidebar Enhancements](https://github.com/titoBouzout/SideBarEnhancements)  
