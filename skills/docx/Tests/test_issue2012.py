import sys
import tempfile
import unittest
from pathlib import Path
from xml.dom import minidom


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from comment import add_comment  # noqa: E402


COMMENTS_RELATIONSHIP_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
)


class Issue2012RegressionTest(unittest.TestCase):
    def test_reuses_renamed_comments_part_and_assigns_unique_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir)
            word_dir = package_dir / "word"
            rels_dir = word_dir / "_rels"
            rels_dir.mkdir(parents=True)

            (word_dir / "comments2.xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:comments xmlns:w="http://schemas.openxmlformats.org/'
                'wordprocessingml/2006/main" '
                'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">'
                '<w:comment w:id="0"><w:p/></w:comment>'
                "</w:comments>",
                encoding="utf-8",
            )
            (rels_dir / "document.xml.rels").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/'
                'package/2006/relationships">'
                '<Relationship Id="rId1" '
                f'Type="{COMMENTS_RELATIONSHIP_TYPE}" '
                'Target="comments2.xml"/>'
                "</Relationships>",
                encoding="utf-8",
            )
            (package_dir / "[Content_Types].xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/'
                'package/2006/content-types">'
                '<Override PartName="/word/comments2.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.comments+xml"/>'
                "</Types>",
                encoding="utf-8",
            )

            new_comment_id, _, _ = add_comment(package_dir, "Second comment")

            comments_path = word_dir / "comments2.xml"
            comments_dom = minidom.parse(str(comments_path))
            comment_ids = sorted(
                int(comment.getAttribute("w:id"))
                for comment in comments_dom.getElementsByTagName("w:comment")
            )

            rels_dom = minidom.parse(str(rels_dir / "document.xml.rels"))
            main_comments_relationships = [
                relationship
                for relationship in rels_dom.getElementsByTagName("Relationship")
                if relationship.getAttribute("Type") == COMMENTS_RELATIONSHIP_TYPE
            ]

            self.assertEqual(new_comment_id, 1)
            self.assertEqual(comment_ids, [0, 1])
            self.assertEqual(len(main_comments_relationships), 1)
            self.assertEqual(
                main_comments_relationships[0].getAttribute("Target"),
                "comments2.xml",
            )
            self.assertFalse((word_dir / "comments.xml").exists())


if __name__ == "__main__":
    unittest.main()