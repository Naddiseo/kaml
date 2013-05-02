KAML - a templating language influenced from SCSS and Jinja


```

// Comments can be like this
/*
	Or like this
*/
// Supports css selector syntax, with parameters for attributes
table.foo(width = "100%" ) {
	// or the attributes can be defined like this
	style = "width: 100%";

	tr {
		th {
			// Raw strings become the innerText of the node
			"Column 1"
		}
		th {
			"Column 2"
		}
	}

	// Control statements begin with a dash
	-for (row in rows) {
		tr {
			// Outside of control statements, variables 
			// have to be given to the "$" function for escaping
			td { ${row.c1} }
			td { ${row.c2} }
		}
	}
}

/* For short (1 argument) functions, the first parameter can be passed without
   the braces, but also must be followed by a semicolon.
*/
label "P&nbsp"; span(itemprop="telephone") ${address.phone}; br;

p {!{
	The "!" function is the "default" filter for raw text, most likely html
	}
	!markdown {
		But a _filter type_ can specified too.
	}
	!(dedent=1){
		The "!" function can dedent this so it's indented only one more than the "p"
	}
}

```
