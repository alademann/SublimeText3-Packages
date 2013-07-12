Sublime Text 2 plugin: Goto Symbol
==================================

This plugin add a command to Sublime Text 2, allowing you to jump to the symbol declaration from a word under your carret or a list of symbols.

Supports
--------

 * PHP
 * JS
 * Python
 * Shell script
 * ... (languages' regexp are customizable via the settings file)

Using
-----

 * Use ctrl+shift+r (command on OSX) to list the indexed symbols.
 * While your cursor is on a word, use alt+click or F2 to jump to the relative symbol's definition of the word.

Notes
-----

 * Sometimes, system doesn't allow using of alt+click, you'll need to remap the key binding or use F2.
 * After the installation, you'll need to restart sublime text 2.
 * You'll need to load a file from one of your folder to get the indexation folders process working.

Installation
------------

The recommmended method of installation is via Package Control. It will download upgrades to your packages automatically.

### Package Control ###

* Follow instructions on http://wbond.net/sublime_packages/package_control
* Install using Package Control: Install > Goto Symbol package

### Using Git ###

Go to your Sublime Text 2 Packages directory and clone the repository using the command below:

    git clone https://github.com/crazycooder/Goto-Symbo "Goto Symbol"

### Download Manually ###

* Download the files using the GitHub .zip download option
* Unzip the files and rename the folder to `Goto Symbol`
* Copy the folder to your Sublime Text 2 Packages directory

Changelog
---------

### 1.2.1 ###
 * Added a reset command.

### 1.2.0 ###
 * Added context menu.
 * Added Goto menu entry.
 * Added line numbol into symbols selecion panel.
 * Added new option "trim_and_order".
 * Added a command to find symbol under caret.
 * Binded new shortcut, F2 now display symbols matches to the word under the caret.
 * Rewamped the way settings are loaded (u'll need to update your user conf if any).
 * Fixed issues on the way folders are loaded.
 * Fixed issues on the way php symbol prefixed by "&" are loaded.
 * Fixed an issue with empty symbol appears after reloading some files.

### 1.1.1 ###
 * Updated the way folders are initialized.

### 1.1.0 ###
 * Added folders indexation.

### 1.0.0 ###
 * First release.

