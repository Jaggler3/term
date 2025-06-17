# Term - terminal internet browser

![term start](https://user-images.githubusercontent.com/11529502/90342254-a60aae00-dfd4-11ea-81ac-064457d04a82.gif)

Term is a terminal-based interactive internet browser that works with a lightweight file format. Term-sites can offer information and interactivity with minimal download sizes. The simple format and set of features allows for wide compatibility to devices that can show a terminal and run Python.
![term usage](https://user-images.githubusercontent.com/11529502/90342257-ab67f880-dfd4-11ea-9e8d-f34f7ba5b74e.gif)

## Using the browser
Install using this command:
```bash
pip3 install termbrowser
```

and start using this command:
```bash
term
```
or manually:
```bash
python3 -m termbrowser
```

## Development
Look at the Makefile for local development scripts.


Open links using their hotkeys ex. 1 for `[1] Link Name`.

Press Escape twice to change the URL to load.
Press Tab to cycle focus of input fields.
Press Enter to submit an input field.
Press Alt(or Option) + Q to unfocus from an input field.

## Important Note
Term Browser sends requests using the header `Content-Type: Term`. Your server can distiguish that the request is coming from the Term Browser through this header.


## File Format
Term files are read line by line. The first line of any term file declares the term version to be used:

```
@termtype:m100
```

The `#` character at the start of a line is used for commenting:

```
# this is a comment!
```

### Elements

There are 5 element types. `cont`, `text`, `link`, `input`, and `action`

Declare an element like so:

```
cont

end
```

Inside of that element, you can place attributes.

```
cont
	-width: 10
	-height: 5
	-border: line
end
```

A `cont` (container) is similar to a `<div>` in HTML.

To specify an element's value, use `:` like so:

```
text:Hello World!
end
# Note any spacing after the `:` is recorded ('text: Hello World!' returns a value of ' Hello World!'). Tabs, spaces, and empty lines separating elements are disregarded and are not required to follow a specific pattern.
```

Input fields can be created like so:

```
input
	-submit: my-action
end
```

## Actions
Actions are blocks of code that you can write in a term file to provide interactivity to it's elements.

To declare an action, use:
```
action: my-action (

)
```

Values are passed to an action code block through a variable named `value`

```
input
	-submit: my-action
end
action: my-action (
	visit("http://localhost/hello?world=" + value)
)
```

## Scripting
The code executed in an action block is not of any specification or language, but is evaluated through [SimpleEval](https://pypi.org/project/simpleeval/).

See [the scripting page](SCRIPTING.md).

## Attributes
Attributes for `cont` include `width`, `height`, `border`, `direction`, and `padding`.

Attributes for `text` include `initial`, `align`, and `style`.

Attributes for `link` include `url`, `align`, and `style`.

Attributes for `input` include `submit`, `width`, `height`, and `padding`.

All elements accept a `name` property, which gives the actions of the page access to it's attributes and value. Accessing by `name` returns the first element in-order of the tree with that name. 

## Responsiveness

Attributes that take in a mathematic value (like `padding` and `width`), can also use a percetange of the screen width or height using the `pc` keyword.

```
# A container that will take up half of the screen width
cont
	-border: line
	-width: 50pc
end
```

# Credits
Term was created by Martin Darazs

## License
MIT License
