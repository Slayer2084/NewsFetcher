import unittest

from src.listeners.cnbc.cnbc import CNBC


# Required Environment Variables: None
class ArticleValidationTestCase(unittest.TestCase):
    def test_article_type_cnbcvideo_or_live_story(self):
        result = {
            "cn:contentClassification": "non-premium",
            "cn:branding": "cnbc",
            "cn:type": "cnbcvideo"
        }

        valid = CNBC._check_if_article_valid(result)

        self.assertFalse(valid)

    def test_article_branding_not_cnbc(self):
        result = {
            "cn:contentClassification": "non-premium",
            "cn:branding": "bbc",
            "cn:type": "article"
        }

        valid = CNBC._check_if_article_valid(result)

        self.assertFalse(valid)

    async def test_article_premium(self):
        result = {
            "cn:contentClassification": "premium",
            "cn:branding": "cnbc",
            "cn:type": "article"
        }

        valid = CNBC._check_if_article_valid(result)

        self.assertFalse(valid)

    async def test_article_not_premium_branding_cnbc_type_not_cnbcvideo_or_live_story(self):
        result = {
            "cn:contentClassification": "non-premium",
            "cn:branding": "cnbc",
            "cn:type": "article"
        }

        valid = CNBC._check_if_article_valid(result)

        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
