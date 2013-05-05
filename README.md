KAML - a templating language influenced from SCSS and Jinja


*	[Syntax](#syntax)
	*	[Overview of Syntax](#overview-of-syntax)
	*	[Comments](#comments)
	*	[Variables](#variables)
	*	[Strings](#strings)
		*	[Quoted Strings](#quoted-strings)
			*	[Variable Interpolation in Quoted Strings](#variable-interpolation-in-quoted-strings)
		*	[Raw Strings](#raw-strings)

<h1 id="syntax">Syntax</h1>

<h2 id="overview-of-syntax">Overview of Syntax</h2>

The syntax was inspired by SCSS, but with the intension of applying to HTML. Thus, bare words are treated as
functions with arguments passed in a strange syntax.
For example, if one wanted to output the html `<div id="foo" class="bar">This is text</div>` one would write something to the effect of:

```

	div#foo.bar {
		"This is text"
	}

```

Internally this is treated as the following function call `div(id = id_fn("foo"), class = class_fn("bar"), inner = ["This is text"])`.
As you can see, basic CSS selector syntax is supported, much as it is in HAML, to shortcut the commonalities of creating HTML.
 
<h2 id="comments">Comments</h2>

Comments are as in C++

```

	// Single line comments
	/*
	 Multi line Comments
	 */


```

<h2 id="variables">Variables</h2>

Variables in KAML have the same form as names in CSS; they have the following requirements

1.	Must not begin with a number
2.	May begin with a dash, an underscore, or ascii "A-Z" (upper or lowercase)
3.	After the first character, may contain any number of letters, numbers, dashes, or underscores.


<h2 id="strings">Strings</h2>

Strings come in three variations in KAML. Single quoted, Double Quoted, and Raw. We'll get back to raw strings later.

<h3 id="quoted-strings">Quoted Strings</h3>

Single and double quoted string behave the same way they do in most programming languages such as C and Python, they are a list of characters
with the exception that some can be escaped with a backslash "\" such as new lines, and quotes ("\n", "\"", '\'').
Also, like in C and Python, adjacent strings are concatenated together, but, unlike in C and Python, strings in KAML are multiline,
so that the following two examples are identical:

```

	// Example 1
	"This is a string on one line"
	"This is another string on the following line"
	
	// Example 2
	"This is a string on one line
	This is another string on the following line"

```

<h4 id="variable-interpolation-in-quoted-strings">Variable Interpolation in Quoted Strings</h4>

Often times in templating languages, one needs to place the value of a variable or expression into the text. 
In KAML this can be achieved in one of 3 ways. For a simple variable one can use the simple `$variable` syntax.

```

	// Supposed the variable "name" has the value of "Bob"
	"Hello $name, nice to meet you"

```

The above example would print:

> Hello Bob, nice to meet you

But sometimes you need a simple expression[^1], for things such as dictionary or list accessing. 
To output the return of an expression one can use `{expression}` syntax.

```

	// mydict = { "a" : "Hello", "b" : "World" }
	"{mydict["a"]} {mydict["b"]}"
	"{1 + 2 - 3 / 4 * 5}"

```

The above example would print:

> Hello World -0.75

The third form of placing variables into a string is the combination of the first two `${expression}`.

```
	// hello = "Hello World"
	"${hello}"

```

Prints out:

> Hello World

<h3 id="raw-strings">Raw Strings</h3>

Like most other languages, KAML starts off in a _code_ state, that is, it assumes that
when it starts reading a file, that it's reading code, not data; (c.f PHP assumes files are data).
The problem with this approach in templating languages like KAML is that one often needs to print
a lot of text data. A few solutions that languages employ to this are multiline strings and heredocs.
The main problem with these two approaches is that it can hide the structure of the data from an
editor, which for HTML editing could hinder development. KAML solves this problem a different way,
with "Raw Strings", or "Raw Blocks." Raw strings are surrounded by triple curly braces, and behave
similarly to other string types, except that the only variable escaping is done with the third `${}` syntax.
A dollar sign, or curly brace by itself are just treated as plain text.

```

	{{{
	Hello World. I have $10.
	let set C = {1,2,3}
	}}}

```

The above would print

>
> Hello World. I have $10.
> let set C = {1,2,3}
> 

[^1]: Although the brace syntax is used for printing expressions, it can also be used to embed any type of code, even more strings which have their own escaped expressions.