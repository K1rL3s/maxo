from maxo.types.emphasized_markup import EmphasizedMarkup
from maxo.types.heading_markup import HeadingMarkup
from maxo.types.highlighted_markup import HighlightedMarkup
from maxo.types.link_markup import LinkMarkup
from maxo.types.monospaced_markup import MonospacedMarkup
from maxo.types.quote_markup import QuoteMarkup
from maxo.types.strikethrough_markup import StrikethroughMarkup
from maxo.types.strong_markup import StrongMarkup
from maxo.types.underline_markup import UnderlineMarkup
from maxo.types.user_mention_markup import UserMentionMarkup

MarkupElements = (
    EmphasizedMarkup
    | HeadingMarkup
    | HighlightedMarkup
    | LinkMarkup
    | MonospacedMarkup
    | QuoteMarkup
    | StrikethroughMarkup
    | StrongMarkup
    | UnderlineMarkup
    | UserMentionMarkup
)
