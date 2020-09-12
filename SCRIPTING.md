# Scripting

## Syntax
Built in functions can be called like `theFunction(params)`
Expressions are separated with a `,` eg `doThis(), doThat()`. 

An example action

```
# Comments must remain outside of an action block
action:myAction(
	var("name", "martin"),
	visit("www.mysite.com/name=" + getvar("name"))
)
```

## Built-In Functions
`visit` opens a URL
`var(name, value)` assigns a value to a variable
`getvar(name)` get a variable value
`action(name)` Call another action as a method
`encode(text)` Encode text to be a valid URI
`action(name)` Call another action to be executed
`debug(text)`  Print to the debug console (open with Alt + K)

## Events
`action:[start]` is called once the page is loaded