# -*- coding: utf-8 -*-

from googletrans import Translator
from odoo import api, models


class TranslationHelper(models.Model):
    """ Class to create translation for selected words"""
    _name = 'translation.helper'
    _description = 'Translation Helper'

    @api.model
    def translate_term(self, args, target_languages):
        """Function to translate the terms"""
        translations = {}
        for target_language in target_languages:
            translator = Translator()
            # Translate the term to the current target language
            translated_text = ''
            try:
                translated_text = translator.translate(args, dest=target_language).text
            except Exception:
                pass
            translations[target_language] = translated_text
        return translations
