# 大辞典原稿補充 2026年11月16日〜29日

2026年11月8日（JST）時点で、当日枠より後の原稿は11月15日までの7日分。本番の `/api/automation/story-version` と main の在庫70件が一致したため、継続承認の範囲で14件を追加する。

指標は在庫終了日を11月29日へ延ばし、毎日17時に異なる原稿を配信できる状態を続けること。用語や絵柄を一枚で学べるよう、説明と日常で試せる行動を組み合わせる。反映後は本番の在庫終了日と毎日の公開・配信画像を既存の監視で確認する。

追加分は西洋占星術6件、タロット5件、数秘・易・ルネーション各1件。占星術・タロットは追加分の11/14件（78.6％）、全体の61/84件（72.6％）。

| 配信日（JST） | 題材 |
| --- | --- |
| 11月16日 | 第4・10ハウスと暮らしの土台 |
| 11月17日 | 隠者が掲げる灯り |
| 11月18日 | 数秘術の2と協力 |
| 11月19日 | 活動宮の始め方 |
| 11月20日 | 悪魔に描かれた鎖 |
| 11月21日 | 月と水星、気持ちと言葉 |
| 11月22日 | 風山漸と段階を踏むこと |
| 11月23日 | 柔軟宮の調整 |
| 11月24日 | 塔の稲妻と冠 |
| 11月25日 | オポジションと両方の希望 |
| 11月26日 | 下弦から新月へ |
| 11月27日 | 節制の小道 |
| 11月28日 | 金星と火星、好みと行動 |
| 11月29日 | 戦車の天蓋と背後の街 |

用語と絵柄を次の資料で照合。暮らしへの応用は各原稿の解釈として書いた。

- ハウス、月・水星・金星・火星、約180度のアスペクト。[Carole Taylor, Introducing Astrology](https://astrology.org.uk/wordpress/wp-content/uploads/IntroducingAstrology.pdf)
- 活動宮・柔軟宮の構成と四つのエレメント。[Astrodienst, The Four Elements](https://www.astro.com/astrology/in_elements_t.htm?lang=e)
- 数秘の2と協力。計算例は架空の日付で、年7・月5・日8の合計20を2に還元。[Numerology.com, Number 2 Meaning](https://www.numerology.com/articles/about-numerology/single-digit-number-2-meaning/)
- 漸の爻と雁の移動。図は上から陽・陽・陰、陽・陰・陰。[易経、James Legge訳 LIII](https://sacred-texts.com/book/the-i-ching/liii-the-kien-hexagram)
- 下弦から新月に向かう月相の順番。[NASA, Moon Phases](https://science.nasa.gov/moon/moon-phases/)
- RWS版の灯り、鎖、稲妻と冠、遠い光と小道、天蓋と街。既存の1909年版画像をプレビューで確認。[隠者](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/ix-the-hermit) [悪魔](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/xv-the-devil) [塔](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/xvi-the-tower) [節制](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/xiv-temperance) [戦車](https://sacred-texts.com/book/the-pictorial-key-to-the-tarot/vii-the-chariot)

- `pytest tests/test_dictionary_celestial.py tests/test_story_program.py -q -p no:cacheprovider` は346件合格。84件×4色の描画を含む。
- 追加14件を実日付のプレビューで生成し、配信順、日付、図、文字の収まりを確認。既存70件と日付計算の設定が元のmainと一致することも確認。
- 内容は一枚一題、短い説明と日常の行動に統一。効果の保証、実績や体験談、販売条件に関する訴求は含まない。
