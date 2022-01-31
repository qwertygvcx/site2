from flask import g
from app.classes.post import *
import bleach
from bleach.linkifier import LinkifyFilter
from functools import partial


allowed_tags = [
	'b',
	'blockquote',
	'br',
	'code',
	'del',
	'em',
	'hr',
	'i',
	'li',
	'ol',
	'p',
	'pre',
	'strong',
	'sub',
	'sup',
	'ul',
	'a',
	'span'
]


allowed_attrs = {
	'a': ['href', 'title', 'target'],
	'i': [],
	'span': ['style']
}


allowed_protocols = [
	'http',
	'https'
]


allowed_styles = ['color']


# apply `nofollow noopener noreferrer` to outgoing links
def noreferrer(attrs, new=False):

	if not attrs[(None, "href")].startswith('/'):
		attrs[(None, "target")] = "_blank"
		attrs[(None, "rel")] = "nofollow noopener noreferrer"

	return attrs


cleaner = bleach.Cleaner(
	tags=allowed_tags,
	attributes=allowed_attrs,
	protocols=allowed_protocols,
	styles=allowed_styles,
	filters=[partial(LinkifyFilter,
			skip_tags=['pre'],
			parse_email=False,
			callbacks=[noreferrer]
		)]
)


def parse(text: str, context=None, db=None) -> str:
	output = ""
	l = [x.strip() for x in text.split('\n')]
	c = 0

	output = green(l, context=context, db=db)
	output = cleaner.clean(output)

	return output


def green(text, context=None, db=None) -> str:

	i = 0
	output = ""
	greentext = False
	while i < len(text):
		if text[i].startswith('>'):
			if greentext:
				if text[i].startswith('>>'):
					newline = linkgen(text[i], context=context, db=db)
				else:
					newline = text[i]
				output += "<br />" + newline
			else:
				if text[i].startswith('>>'):
					newline = linkgen(text[i], context=context, db=db)
				else:
					newline = text[i]
				output += "<blockquote>" + newline
				greentext = True
		else:
			if greentext:
				# close greentext block
				output += "</blockquote>"
				greentext = False

			output += "<p>" + text[i] + "</p>"

		i += 1

	if greentext:
		output += "</blockquote>"
		greentext = False

	return output


def linkgen(string, context=None, db=None) -> str:

	if not db:
		db = g.db

	posts = {}
	same_thread = False

	text = string.lstrip('>').split()[0]

	try:
		if context and text.lower() == "op":
			pid = int(context.parent_id)
		else:
			pid = int(text)

		post = posts.get(pid)

		if post not in posts:
			post = db.query(Post).filter_by(id=pid).first()
			posts[pid] = post

		if not post:
			return string

		if context:
			if post.is_top_level:
				same_thread = int(context.parent_id) == post.id
			else:
				same_thread = int(context.parent_id) == post.parent_id
		else:
			same_thread = False

		if same_thread:

			if post.is_top_level:
				href = post.permalink + "#" + str(post.id)
			else:
				href = post.permalink

			link = '<a class="post-mention" href="{}">>>{}'.format(href, post.id)

			if post.is_top_level:
				link += ' (OP)'

			link += '</a>'

			if context.id not in post.quoted_by:
				post.quoted_by.append(int(context.id))
				db.add(post)
		else:
			link = '<a class="post-mention" href="{}" target="_blank">>>>/{}/{}</a>'.format(post.permalink, post.board.name, post.id)

		output = link + "<br />"
		if len(string.split()) > 1:
			output += "&gt;" + " ".join(string.split()[1:])

		return output

	except Exception as e:
		return string
