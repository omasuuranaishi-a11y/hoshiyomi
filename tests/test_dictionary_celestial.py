from copy import deepcopy
from datetime import timedelta
import pytest
from backend.story_program import DICTIONARY
from backend.story_dictionary_celestial import START,DESIGN,variant_for_day
from backend.story_program_render import render_program,validate_program_asset

@pytest.mark.parametrize('offset,variant',[(0,'C'),(1,'D'),(2,'A'),(3,'B')])
@pytest.mark.parametrize('index',range(14))
def test_entire_stock_all_palettes(tmp_path,index,offset,variant):
    content=deepcopy(DICTIONARY['rounds'][index//7][index%7]);original=deepcopy(content)
    content.update(slot='evening',title='おますの占い大辞典')
    day=START+timedelta(days=offset)
    path=render_program(content,day,tmp_path/f'{index}-{variant}.jpg')
    assert validate_program_asset(path,content,day)['design']==DESIGN
    assert content['render_check']['variant']==variant
    assert all(content[k]==v for k,v in original.items())

def test_four_color_rotation_across_year_boundary():
    days=[START+timedelta(days=i) for i in range(500)]
    assert all(variant_for_day(d)==variant_for_day(d+timedelta(days=4)) for d in days)
    assert all(variant_for_day(d)!=variant_for_day(d+timedelta(days=1)) for d in days)
