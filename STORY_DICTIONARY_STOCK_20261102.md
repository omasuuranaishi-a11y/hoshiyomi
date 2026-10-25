# 大辞典原稿補充：2026年11月2日〜11月15日

確認日：2026年10月25日（Asia/Tokyo）。在庫終了11月1日との差が7日になったため、監視指示の継続承認に従い14件を追加する。

## KPI宣言

- 対象：毎日17時の「おますの占い大辞典」の在庫切れ防止。
- 指標：異なる原稿の在庫終了日を11月1日から11月15日へ、総数を56件から70件へ延長。
- 読者の変化：占術の用語や絵柄を身近な行動に結びつけ、一日一つ学べる状態を続ける。
- 仮説：定めた閾値で補充すれば原稿の循環による意図しない再利用を防げる。閲覧数や売上への効果は未測定。
- 根拠：使用者の監視・補充指示、10月25日の本番 story-version とリポジトリの在庫56件。
- 方針照合：追加14件は占星術6件・タロット5件・その他3件（78.6％）。総在庫も占星術・タロット50/70件（71.4％）。手相・廃止コラム・過去枠の追加投稿は含めない。
- 出荷条件：機械・文体・事実・表示上の訴求を点検し、描画検査後にmainへ反映する。
- 計測：本番の在庫終了日、毎枠の公開IDと配信画像を既存監視で確認する。

## 配信順

| JST日付 | 内容 |
| --- | --- |
| 2026-11-02 | 西洋占星術｜第1ハウス |
| 2026-11-03 | タロット｜女教皇の絵柄 |
| 2026-11-04 | 数秘術｜9という数 |
| 2026-11-05 | 西洋占星術｜第12ハウス |
| 2026-11-06 | タロット｜太陽の絵柄 |
| 2026-11-07 | 西洋占星術｜水星と伝え方 |
| 2026-11-08 | ルネーション占星術｜満ち欠け |
| 2026-11-09 | 西洋占星術｜金星と好きの理由 |
| 2026-11-10 | タロット｜月の絵柄 |
| 2026-11-11 | 西洋占星術｜不動宮の続け方 |
| 2026-11-12 | 易｜乾為天（けんいてん） |
| 2026-11-13 | タロット｜審判の絵柄 |
| 2026-11-14 | 西洋占星術｜第3・9ハウス |
| 2026-11-15 | タロット｜死神の絵柄 |

## 根拠と解釈の区別

用語・絵柄の事実を以下で照合した。日本語の見出し、生活への応用、四つのエレメント別の問いは今回のオリジナルの解釈であり、資料の直訳や効果の実証ではない。

- 第1ハウスの自己表現・第7との対置：[Astrodienst, House One](https://www.astro.com/astrowiki/en/1st_House)。
- 第3・9ハウスの学びと視野、第6・12ハウスの日常と退避：[Astrodienst, House](https://www.astro.com/astrowiki/en/House)、[Faculty of Astrological Studies, Introducing Astrology（Carole Taylor）](https://astrology.org.uk/wordpress/wp-content/uploads/IntroducingAstrology.pdf)。
- 水星の思考・情報・伝達：[Astrodienst, Mercury](https://www.astro.com/astrowiki/en/Mercury)。
- 金星の喜びと関係の象徴：[Astrodienst, Venus Return Chart](https://www.astro.com/astrowiki/en/Venus_Return_Chart)。
- 不動宮の四星座と維持する働き：[Astrodienst, Fixed](https://www.astro.com/astrowiki/en/Fixed)。
- 数秘9の完了と思いやり：[Numerology.com, Number 9 Meaning](https://www.numerology.com/articles/about-numerology/single-digit-number-9-meaning/)。計算例1990年1月16日は架空の例で、年19→1、月1、日16→7、合計9を独立確認。
- 乾為天の六本の陽爻、龍と時機：[易経・James Legge訳 Section I: Khien](https://sacred-texts.com/book/the-i-ching/shell/section-i-khien)。
- 月の明るい部分が増減する順序：[NASA, Moon Phases](https://science.nasa.gov/moon/moon-phases/)。計画への重ね方は象徴的な提案。11月8日が新月・満月であるとは書いていない。
- 女教皇の白黒の柱・巻物・三日月：[A. E. Waite, II. The High Priestess](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/ii-the-high-priestess)。
- 太陽の子ども・白馬：[A. E. Waite, XIX. The Sun](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/xix-the-sun)。
- 月の犬・狼・塔の間の道：[A. E. Waite, XVIII. The Moon](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/xviii-the-moon)。
- 審判の天使・ラッパ・応える人物：[A. E. Waite, XX. The Last Judgement](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/xx-the-last-judgement)。
- 死神の旗を持つ騎士・遠い太陽・変化：[A. E. Waite, XIII. Death](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/xiii-death)。
- タロット絵は既存の `backend/assets/tarot/major-XX-rws1909-v1.jpeg` をそのまま使い、番号II・XIII・XVIII・XIX・XXと絵柄をプレビューで照合。素材の記録は [SOURCES.md](backend/assets/tarot/SOURCES.md)。

## 検品記録

- 機械：`pytest tests/test_dictionary_celestial.py tests/test_story_program.py -q -p no:cacheprovider` は **290 passed**。全70件×4色＝280描画を含む。
- 日付：追加14件を11月2〜15日の各日で個別に生成し、配信順、日付、品質検査合格を確認。
- 不変性：元の56件、cycle、start_date、除外設定をHEADと比較し一致。朝と運勢のコード、画像素材、投稿ワークフロー、コラムは変更しない。
- 文体：一枚一話題、短い解説と具体的な行動で統一し、上記14枚の実画像で文字切れ、重なり、装飾との干渉、基本RWS絵柄を確認。
- 事実：上記資料と照合。性格・未来を断定せず「読む」「象徴」「考える」の範囲に留める。
- 訴求：効果保証、実績・証言の創作、価格・販売期限、顧客情報、医療・投資判断の訴求なし。事前選別で修正すべき項目は見つからなかった。
- 個別承認：使用者が指定した「残り7日以下で14日分補充・テスト後main反映」の継続承認を適用。自動投稿や重複防止の条件は変更しない。
