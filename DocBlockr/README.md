DocBlockr is a package for [Sublime Text 2 & 3][sublime] which makes writing documentation a breeze. DocBlockr supports **JavaScript**, **PHP**, **ActionScript**, **CoffeeScript**, **TypeScript**, **Java**, **Groovy**, **Objective C**, **C**, **C++** and **Rust**.

## Installation ##

### With Package Control ###

With [Package Control][package_control] installed, you can install DocBlockr from inside Sublime Text itself. Open the Command Palette and select "Package Control: Install Package", then search for DocBlockr and you're done!

## Feature requests & bug reports ##

You can leave either of these things [here][issues]. Pull requests are welcomed heartily, but please read [CONTRIBUTING.md][contrib] first! Basically: in this repo, the main development branch is `develop` and the stable 'production' branch is `master`. Please remember to base your branch from `develop` and issue the pull request back to that branch.

## Changelog ##

- **v2.12.2**, *11 Apr 2014*
  - Fix for PHP autocompletions
  - Fix `@name` completion for Javascript
- **v2.12.1**, *4 Mar 2014*
  - Fix for Sublime Text 3
- **v2.12.0**, *4 Mar 2014*
  - Adds support for **TypeScript**, thanks to [Marc-Antoine Parent](https://github.com/maparent)
  - Adds option to add a spacer line after the description (`"jsdocs_spacer_between_sections": "after_description"`), thanks to [Milos Levacic](https://github.com/levacic)
  - PHP autocompletions support only the [PSR-5](https://github.com/phpDocumentor/fig-standards/blob/master/proposed/phpdoc.md) tags, thanks to [Gary Jones](https://github.com/GaryJones)
  - Fix scope issues for Java autocompletions, thanks to [Dominique Wahli](https://github.com/bizoo)
  - Fix for reflowing paragraphs when no rulers are set.
- **v2.11.7**, *3 Nov 2013*
  - Added support for triple `///`, `//!` and `/*!` style comments, thanks to [Jordi Boggiano](https://github.com/seldaek).
  - Added basic **Rust** support, again thanks to Jordi Boggiano.
  - Added an option to use short names for bools and ints (`jsdocs_short_primitives`), thanks to [Mat Gadd](https://github.com/drarok).
  - Fixed a bug with per-section indenting, again thanks to Mat Gadd.
  - Improved handling of Java return type detection, thanks to [Ben Linskey](https://github.com/blinskey)
- **v2.11.6**, *14 Aug 2013*
  - Predefined `@author` tags do not get parsed for column spacing
  - Handles the case when an arguments list contains a comma, for example, within a default value
  - A new keybinding for Windows to re-parse a doc block (<kbd>Alt+W</kbd>)
  - Fixes a regression that some function names were not being parsed correctly

Older history can be found in [the history file](https://github.com/spadgos/sublime-jsdocs/blob/master/HISTORY.md).

## Show your love

[![Click here to lend your support to: DocBlockr and make a donation at pledgie.com!](https://pledgie.com/campaigns/16316.png?skin_name=chrome)](http://pledgie.com/campaigns/16316)


## Usage ##

> Below are some examples of what the package does. Note that there are no keyboard shortcuts required to trigger these completions - just type as normal and it happens for you!

### Docblock completion ###

Pressing **enter** or **tab** after `/**` (or `###*` for Coffee-Script) will yield a new line and will close the comment.

![](http://spadgos.github.io/sublime-jsdocs/images/basic.gif)

Single-asterisk comment blocks behave similarly:

![](http://spadgos.github.io/sublime-jsdocs/images/basic-block.gif)

### Function documentation ###

However, if the line directly afterwards contains a function definition, then its name and parameters are parsed and some documentation is automatically added.

![](http://spadgos.github.io/sublime-jsdocs/images/function-template.gif)

You can then press `tab` to move between the different fields.

If you have many arguments, or long variable names, it might be useful to spread your arguments across multiple lines. DocBlockr will handle this situation too:

![](http://spadgos.github.io/sublime-jsdocs/images/long-args.gif)

In languages which support [type hinting][typehinting] or default values, then those types are prefilled as the datatypes.

![](http://spadgos.github.io/sublime-jsdocs/images/type-hinting.gif)

DocBlockr will try to make an intelligent guess about the return value of the function.

- If the function name is or begins with "set" or "add", then no `@return` is inserted.
- If the function name is or begins with "is" or "has", then it is assumed to return a `Boolean`.
- In Javascript, if the function begins with an uppercase letter then it is assumed that the function is a class definition. No `@return` tag is added.
- In PHP, some of the [magic methods][magicmethods] have their values prefilled:
  - `__construct`, `__destruct`, `__set`, `__unset`, `__wakeup` have no `@return` tag.
  - `__sleep` returns an `Array`.
  - `__toString` returns a `string`.
  - `__isset` returns a `bool`.

### Variable documentation ###

If the line following your docblock contains a variable declaration, DocBlockr will try to determine the data type of the variable and insert that into the comment.

If you press `shift+enter` after the opening `/**` then the docblock will be inserted inline.

![](http://spadgos.github.io/sublime-jsdocs/images/vars.gif)

DocBlockr will also try to determine the type of the variable from its name. Variables starting with `is` or `has` are assumed to be booleans, and `callback`, `cb`, `done`, `fn`, and `next` are assumed to be functions. If you use your own variable naming system (eg: hungarian notation: booleans all start with `b`, arrays start with `arr`), you can define these rules yourself. Modify the `jsdocs_notation_map` setting *(in `Base File.sublime-settings`)* like so:

```json
{
    "jsdocs_notation_map": [
        {
            "prefix": "b", // a prefix, matches only if followed by an underscore or A-Z
            "type": "bool" // translates to "Boolean" in javascript, "bool" in PHP
        },
        {
            "regex": "tbl_?[Rr]ow", // any arbitrary regex to test against the variable name
            "type": "TableRow"      // you can add your own types
        }
    ]
}
```

The notation map can also be used to add arbitrary tags, according to your own code conventions. For example, if your conventions state that functions beginning with an underscore are private, you could add this to the `jsdocs_notation_map`:

```json
{
    "prefix": "_",
    "tags": ["@private"]
}
```

### Comment extension ###

Pressing enter inside a docblock will automatically insert a leading asterisk and maintain your indentation.

![](http://spadgos.github.io/sublime-jsdocs/images/auto-indent.gif)

![](http://spadgos.github.io/sublime-jsdocs/images/auto-indent-2.gif)

This applies to docblock comments `/** like this */` as well as inline double-slash comments `// like this`

![](http://spadgos.github.io/sublime-jsdocs/images/single-line.gif)

In either case, you can press `shift+enter` to stop the automatic extension.

Oftentimes, when documenting a parameter, or adding a description to a tag, your description will cover multiple lines. If the line you are on is directly following a tag line, pressing `tab` will move the indentation to the correct position.

![](http://spadgos.github.io/sublime-jsdocs/images/deep-indent.gif)

### Comment decoration ###

If you write a double-slash comment and then press `Ctrl+Enter`, DocBlockr will 'decorate' that line for you.

    // Foo bar baz<<Ctrl+Enter>>

    -- becomes

    /////////////////
    // Foo bar baz //
    /////////////////

### Reparsing a DocBlock ###

Sometimes, you'll perform some action which clears the fields (sections of text which you can navigate through using `tab`). This leaves you with a number of placeholders in the DocBlock with no easy way to jump to them.

With DocBlockr, you can reparse a comment and reactivate the fields by pressing the hotkey `Alt+Shift+Tab` in OS X or Linux, or `Alt+W` in Windows

### Reformatting paragraphs ###

Inside a comment block, hit `Alt+Q` to wrap the lines to make them fit within your rulers. If you would like subsequent lines in a paragraph to be indented, you can adjust the `jsdocs_indentation_spaces_same_para` setting. For example, a value of `3` might look like this:

    /**
     * Duis sed arcu non tellus eleifend ullamcorper quis non erat. Curabitur
     *   metus elit, ultrices et tristique a, blandit at justo.
     * @param  {String} foo Lorem ipsum dolor sit amet.
     * @param  {Number} bar Nullam fringilla feugiat pretium. Quisque
     *   consectetur, risus eu pellentesque tincidunt, nulla ipsum imperdiet
     *   massa, sit amet adipiscing dolor.
     * @return {[Type]}
     */

### Adding extra tags ###

Finally, typing `@` inside a docblock will show a completion list for all tags supported by [JSDoc][jsdoc], the [Google Closure Compiler][closure], [YUIDoc][yui] or [PHPDoc][phpdoc]. Extra help is provided for each of these tags by prefilling the arguments each expects. Pressing `tab` will move the cursor to the next argument.

## Configuration ##

You can access the configuration settings by selecting `Preferences -> Package Settings -> DocBlockr`.

*The `jsdocs_*` prefix is a legacy from days gone by...*

- `jsdocs_indentation_spaces` *(Number)* The number of spaces to indent after the leading asterisk.

        // jsdocs_indentation_spaces = 1
        /**
         * foo
         */

        // jsdocs_indentation_spaces = 5
        /**
         *     foo
         */

- `jsdocs_align_tags` *(String)* Whether the words following the tags should align. Possible values are `'no'`, `'shallow'` and `'deep'`

    > For backwards compatibility, `false` is equivalent to `'no'`, `true` is equivalent to `'shallow'`

    `'shallow'` will align only the first words after the tag. eg:

        @param    {MyCustomClass} myVariable desc1
        @return   {String} foo desc2
        @property {Number} blahblah desc3

    `'deep'` will align each component of the tags, eg:

        @param    {MyCustomClass} myVariable desc1
        @return   {String}        foo        desc2
        @property {Number}        blahblah   desc3


- `jsdocs_extra_tags` *(Array.String)* An array of strings, each representing extra boilerplate comments to add to *functions*. These can also include arbitrary text (not just tags).

        // jsdocs_extra_tags = ['This is a cool function', '@author nickf', '@version ${1:[version]}']
        /**<<enter>>
        function foo (x) {}

        /**
         * [foo description]
         * This is a cool function
         * @author nickf
         * @version [version]
         * @param  {[type]} x [description]
         * @return {[type]}
         */
        function foo (x) {}

    Basic variable substitution is supported here for the variables `date` and `datetime`, wrapped in double curly brackets.

        // jsdocs_extra_tags = ['@date {{date}}', '@anotherdate {{datetime}}']
        /**<<enter>>
        function foo() {}

        /**
         * [foo description]
         * @date     2013-03-25
         * @datetime 2013-03-25T21:16:25+0100
         * @return   {[type]}
         */

- `jsdocs_extra_tags_go_after` *(Boolean)* If true, the extra tags are placed at the end of the block (after param/return). Default: `false`

- `jsdocs_extend_double_slash` *(Boolean)* Whether double-slash comments should be extended. An example of this feature is described above. Default: `true`

- `jsdocs_deep_indent` *(Boolean)* Whether pressing tab at the start of a line in docblock should indent to match the previous line's description field. An example of this feature is described above. Default: `true`

- `jsdocs_notation_map` *(Array)* An array of notation objects. Each notation object must define either a `prefix` OR a `regex` property, and a `type` property.

- `jsdocs_return_tag` *(String)* The text which should be used for a `@return` tag. By default, `@return` is used, however this can be changed to `@returns` if you use that style.

- `jsdocs_spacer_between_sections` *(Boolean|String)* If true, then extra blank lines are inserted between the sections of the docblock. If set to `"after_description"` then a spacer will only be added between the description and the first tag. Default: `false`.

- `jsdocs_indentation_spaces_same_para` *(Number)* Described above in the *Reformatting paragraphs* section. Default: `1`

- `jsdocs_autoadd_method_tag` *(Boolean)* Add a `@method` tag to docblocks of functions. Default: `false`

- `jsdocs_simple_mode` *(Boolean)* If true, DocBlockr won't add a template when creating a doc block before a function or variable. Useful if you don't want to write Javadoc-style, but still want your editor to help when writing block comments. Default: `false`

- `jsdocs_lower_case_primitives` *(Boolean)* If true, primitive data types are added in lower case, eg "number" instead of "Number". Default: `false`

- `jsdocs_short_primitives` *(Boolean)* If true, the primitives `Boolean` and `Integer` are shortened to `Bool` and `Int`. Default: `false`

- `jsdocs_newline_after_block` *(Boolean)* If true, an extra line break is added after the end of a docblock to separate it from the code. Default `false`

This is my first package for Sublime Text, and the first time I've written any Python, so I heartily welcome feedback and [feature requests or bug reports][issues].

[closure]: http://code.google.com/closure/compiler/docs/js-for-compiler.html
[contrib]: blob/master/CONTRIBUTING.md
[issues]: https://github.com/spadgos/sublime-jsdocs/issues
[jsdoc]: http://code.google.com/p/jsdoc-toolkit/wiki/TagReference
[magicmethods]: http://www.php.net/manual/en/language.oop5.magic.php
[package_control]: http://wbond.net/sublime_packages/package_control
[phpdoc]: http://phpdoc.org/
[sublime]: http://www.sublimetext.com/
[tags]: https://github.com/spadgos/sublime-jsdocs/tags
[typehinting]: http://php.net/manual/en/language.oop5.typehinting.php
[yui]: http://yui.github.com/yuidoc/syntax/index.html
