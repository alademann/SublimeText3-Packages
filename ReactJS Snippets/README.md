reactjs-snippets
================

Simple ReactJS snippets

## Tab Triggers

###rcl:

	var ${1:class} = React.createClass({
		render: function() {
			<${2:div} ${3:className="${1:class}"}>${4}</${2:div}>
		}
	});