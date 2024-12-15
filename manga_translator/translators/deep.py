import logging
from deep_translator import GoogleTranslator
import asyncio
import re
from typing import List
from .common import CommonTranslator, MissingAPIKeyException
from .keys import OPENAI_API_KEY, OPENAI_HTTP_PROXY, OPENAI_API_BASE

CONFIG = None

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleTranslatorWrapper(CommonTranslator):
    _LANGUAGE_CODE_MAP = {
        'CHS': 'zh-CN',
        'CHT': 'zh-TW',
        'CSY': 'cs',
        'NLD': 'nl',
        'ENG': 'en',
        'FRA': 'fr',
        'DEU': 'de',
        'HUN': 'hu',
        'ITA': 'it',
        'JPN': 'ja',
        'KOR': 'ko',
        'PLK': 'pl',
        'PTB': 'pt',
        'ROM': 'ro',
        'RUS': 'ru',
        'ESP': 'es',
        'TRK': 'tr',
        'UKR': 'uk',
        'VIN': 'vi',
        'CNR': 'sr-ME',
        'SRP': 'sr',
        'HRV': 'hr',
        'ARA': 'ar',
        'THA': 'th',
        'IND': 'id'
    }

    _ONOMATOPEES = {
        'UGH',
        'URGH'
    }

    def __init__(self):
        super().__init__()

    def parse_args(self, args):
        self.config = args.gpt_config

    def _config_get(self, key: str, default=None):
        if not self.config:
            return default
        return self.config.get('google_translator.' + key, self.config.get(key, default))

    def _clean_text(self, text: str) -> str:
        # Ne pas enlever les caractères non occidentaux
        return text

    def _split_ascii_non_ascii(self, text: str) -> List[str]:
        """
        Séparer un texte en fragments ASCII et non-ASCII.
        """
        pattern = r'([^\x00-\x7F]+)'  # Regex pour capturer les caractères non-ASCII
        return re.split(pattern, text)

    async def _translate(self, from_lang: str, to_lang: str, queries: List[str]) -> List[str]:
        translations = []
        for i, query in enumerate(queries):
            fragments = self._split_ascii_non_ascii(query)
            translated_fragments = []

            for fragment in fragments:
                # Si le fragment est entièrement non-ASCII ou un caractère spécial, on le conserve tel quel
                if not any(c.isascii() for c in fragment) or fragment in self._ONOMATOPEES or len(fragment.strip()) == 1:
                    logger.info(f"[GoogleTranslatorWrapper] Fragment non traduit : '{fragment}'")
                    translated_fragments.append(fragment)
                else:
                    # Traduire uniquement les fragments ASCII
                    logger.info(f"[GoogleTranslatorWrapper] Translating fragment into {to_lang}")
                    translated = await asyncio.to_thread(
                        GoogleTranslator(source=from_lang, target=to_lang).translate, fragment
                    )
                    logger.info(f"[GoogleTranslatorWrapper] {fragment} => {translated}")
                    translated_fragments.append(translated)

            # Réassembler les fragments traduits et non traduits
            final_translation = ''.join(translated_fragments)
            translations.append(final_translation)
            #file_name = os.path.basename(file_path)
            logger.info(f"[GoogleTranslatorWrapper] {i}: {query} => {final_translation}")

        return translations

# Example usage
async def main():
    translator = GoogleTranslatorWrapper()
    from_lang = 'ENG'
    to_lang = 'FRA'
    queries = ["Hello, how are you?", "What is your name?", "こんにちは、元気ですか？", "UGH", "URGH", "A", "こ", "WHAT'S THIS...⁈"]
    translations = await translator._translate(from_lang, to_lang, queries)
    print(translations)

if __name__ == "__main__":
    asyncio.run(main())

