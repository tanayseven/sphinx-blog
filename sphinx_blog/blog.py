import re
from datetime import datetime
from typing import TypedDict, Optional

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx
from sphinx.directives import Node
from sphinx.environment import BuildEnvironment
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import set_source_info
from sphinx.writers.html5 import HTML5Translator
from sphinx.writers.texinfo import TexinfoTranslator
from sphinx.writers.text import TextTranslator


class PostNode(nodes.Element):
    ...


def visit_post_node_html(translator: HTML5Translator, node: PostNode):
    ...


def depart_post_node_html(translator: HTML5Translator, node: PostNode):
    ...


def visit_post_node_texinfo(translator: TexinfoTranslator, node: PostNode):
    ...


def depart_post_node_texinfo(translator: TexinfoTranslator, node: PostNode):
    translator.depart_section(node)


def visit_post_node_text(translator: TextTranslator, node: PostNode):
    translator.visit_section(node)


def depart_post_node_text(translator: TextTranslator, node: PostNode):
    translator.depart_section(node)


def _fetch_date_from_file(node):
    date_patten = re.compile(r"(\d{4}-\d{2}-\d{2})")
    dates = date_patten.findall(node.source)
    date_str = dates[0] if dates else None
    date = datetime.strptime(date_str, "%Y-%m-%d")
    node["publish_date"] = date
    return date


class PostDirective(SphinxDirective):
    has_content = False
    option_spec = {"tags": str, "category": str, "author": str, "draft": bool}

    def run(self) -> list[Node]:
        node = PostNode()
        node.document = self.state.document
        set_source_info(self, node)
        date = _fetch_date_from_file(node)
        node.append(
            nodes.line(text=f"Published on: {date.strftime('%d %B %Y')}"),
        )
        node.append(nodes.transition())
        titles = [x for x in node.document.traverse() if hasattr(x, "title")]
        title = titles[0].astext() if titles else None
        self.state.nested_parse(self.content, self.content_offset, node)
        if not hasattr(self.env, "all_posts"):
            self.env.all_posts = []
        target_id = "post-%d" % self.env.new_serialno("post")
        target_node = nodes.target("", "", ids=[target_id])
        self.env.all_posts.append(
            {
                "title": title,
                "docname": self.env.docname,
                "target": target_node,
                "date": date,
                "node": node,
                "author": self.options["author"],
                "tags": [x.strip(" ") for x in self.options["tags"].split(",")],
                "draft": self.options.get("draft"),
            }
        )
        return [target_node, node]


class AllPostsNode(nodes.General, nodes.Element):
    ...


def visit_all_posts_node_html(translator: HTML5Translator, node: PostNode):
    translator.visit_section(node)


def depart_all_posts_node_html(translator: HTML5Translator, node: PostNode):
    translator.depart_section(node)


def visit_all_posts_node_texinfo(translator: TexinfoTranslator, node: PostNode):
    translator.visit_section(node)


def depart_all_posts_node_texinfo(translator: TexinfoTranslator, node: PostNode):
    translator.depart_section(node)


def visit_all_posts_node_text(translator: TextTranslator, node: PostNode):
    translator.visit_section(node)


def depart_all_posts_node_text(translator: TextTranslator, node: PostNode):
    translator.depart_section(node)


class AllPostsDirective(Directive):
    def run(self) -> list[Node]:
        return [AllPostsNode()]


def process_post_nodes(app: Sphinx, doctree: nodes.document, fromdocname: str):
    env = app.builder.env

    if hasattr(env, "all_posts"):
        env.all_posts = sorted(
            env.all_posts, key=lambda post: post["date"], reverse=True
        )

    for node in doctree.traverse(AllPostsNode):
        if not hasattr(env, "all_posts"):
            continue
        content = []
        for post_meta in env.all_posts:
            if post_meta["draft"]:
                continue
            formatted_post_date = datetime.strftime(post_meta["date"], "%d %B %Y")

            # Set up a section for the post content
            post_section = nodes.section()
            post_section.attributes["ids"] = [f"{post_meta['title'].replace(' ', '-')}"]

            # Add the post title
            title = nodes.title()
            reference = nodes.reference("", "")
            reference["refdocname"] = post_meta["docname"]
            reference["refuri"] = app.builder.get_relative_uri(
                fromdocname, post_meta["docname"]
            )
            reference["refuri"] += "#" + post_meta["target"]["refid"]
            reference.append(nodes.Text(f"{post_meta['title']}"))
            title += reference
            post_section.append(title)

            # Add date and append it to the paragraph
            post_section += nodes.paragraph(text=f"{formatted_post_date}")

            # Transition is needed for the next post
            post_section.append(nodes.transition())
            content.append(post_section)
        node.replace_self(content)


def purge_post_nodes(app: Sphinx, env: BuildEnvironment, docname: str):
    if not hasattr(env, "all_posts"):
        return
    env.all_posts = [post for post in env.all_posts if post["docname"] != docname]


def merge_post_nodes(app: Sphinx, env: BuildEnvironment, docname: str, others: list):
    if not hasattr(env, "all_posts"):
        env.all_posts = []
    if hasattr(docname, "all_posts"):
        docname.all_posts.extend(env.all_posts)


class Metadata(TypedDict):
    version: Optional[str]
    parallel_read_safe: Optional[bool]
    parallel_write_safe: Optional[bool]


def setup(app: Sphinx) -> Metadata:
    app.add_node(
        AllPostsNode,
        html=(visit_all_posts_node_html, depart_all_posts_node_html),
        texinfo=(visit_all_posts_node_texinfo, depart_all_posts_node_texinfo),
        text=(visit_post_node_text, depart_all_posts_node_text),
    )
    app.add_node(
        PostNode,
        html=(visit_post_node_html, depart_post_node_html),
        texinfo=(visit_post_node_texinfo, depart_post_node_texinfo),
        text=(visit_post_node_text, depart_post_node_text),
    )
    app.add_directive("all-posts", AllPostsDirective)
    app.add_directive("post", PostDirective)
    app.connect("doctree-resolved", process_post_nodes)
    app.connect("env-purge-doc", purge_post_nodes)
    app.connect("env-merge-info", merge_post_nodes)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
