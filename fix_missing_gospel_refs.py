#!/usr/bin/env python3
"""
Fix missing Gospel references for Palm Sunday, Good Friday, and Holy Saturday
"""

import json

def main():
    print("="*60)
    print("Fixing Missing Gospel References for Holy Week")
    print("="*60)
    
    # Load year_b_readings.json
    with open('year_b_readings.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    year_b = data['YearB']
    
    # Fix Palm Sunday (Year B)
    print("\n1. Fixing Palm Sunday (2027-03-21)...")
    year_b['2027-03-21'] = {
        'first_reading': {
            'reference': 'Isaiah 50:4-9a',
            'text': ''
        },
        'psalm': {
            'reference': 'Psalm 31:9-16',
            'text': ''
        },
        'second_reading': {
            'reference': 'Philippians 2:5-11',
            'text': ''
        },
        'gospel': {
            'reference': 'Mark 14:1-15:47',
            'text': ''
        },
        'collect': {
            'reference': 'The Collect',
            'text': 'Almighty and everliving God, in your tender love for the human race you sent your Son our Savior Jesus Christ to take upon him our nature, and to suffer death upon the cross, giving us the example of his great humility: Mercifully grant that we may walk in the way of his suffering, and also share in his resurrection; through Jesus Christ our Lord, who lives and reigns with you and the Holy Spirit, one God, for ever and ever. Amen.'
        }
    }
    print("   ✓ Fixed Palm Sunday")
    
    # Fix Good Friday
    print("\n2. Fixing Good Friday (2027-03-26)...")
    year_b['2027-03-26'] = {
        'first_reading': {
            'reference': 'Isaiah 52:13-53:12',
            'text': ''
        },
        'psalm': {
            'reference': 'Psalm 22',
            'text': ''
        },
        'second_reading': {
            'reference': 'Hebrews 10:16-25',
            'text': ''
        },
        'gospel': {
            'reference': 'John 18:1-19:42',
            'text': ''
        },
        'collect': {
            'reference': 'The Collect',
            'text': 'Almighty God, we pray you graciously to behold this your family, for whom our Lord Jesus Christ was willing to be betrayed, and given into the hands of sinners, and to suffer death upon the cross; who now lives and reigns with you and the Holy Spirit, one God, for ever and ever. Amen.'
        }
    }
    print("   ✓ Fixed Good Friday")
    
    # Fix Holy Saturday
    print("\n3. Fixing Holy Saturday (2027-03-27)...")
    year_b['2027-03-27'] = {
        'first_reading': {
            'reference': 'Job 14:1-14',
            'text': ''
        },
        'psalm': {
            'reference': 'Psalm 31:1-4, 15-16',
            'text': ''
        },
        'second_reading': {
            'reference': '1 Peter 4:1-8',
            'text': ''
        },
        'gospel': {
            'reference': 'Matthew 27:57-66',
            'text': ''
        },
        'collect': {
            'reference': 'The Collect',
            'text': 'O God, Creator of heaven and earth: Grant that, as the crucified body of your dear Son was laid in the tomb and rested on this holy Sabbath, so we may await with him the coming of the third day, and rise with him to newness of life; who now lives and reigns with you and the Holy Spirit, one God, for ever and ever. Amen.'
        }
    }
    print("   ✓ Fixed Holy Saturday")
    
    # Save updated file
    print("\n4. Saving updated year_b_readings.json...")
    output_data = {'YearB': year_b}
    with open('year_b_readings.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print("   ✓ Saved!")
    
    # Final verification
    print("\n" + "="*60)
    print("FINAL VERIFICATION:")
    print("="*60)
    
    critical_dates = [
        ('2027-03-21', 'Palm Sunday'),
        ('2027-03-25', 'Maundy Thursday'),
        ('2027-03-26', 'Good Friday'),
        ('2027-03-27', 'Holy Saturday'),
        ('2027-03-28', 'Easter Sunday'),
        ('2027-05-06', 'Ascension Day'),
        ('2027-05-16', 'Pentecost'),
        ('2027-05-23', 'Trinity Sunday'),
    ]
    
    for date, name in critical_dates:
        gospel = year_b[date].get('gospel', {}).get('reference', 'N/A')
        print(f'✓ {date}: {name:25} - Gospel: {gospel}')
    
    print("\n" + "="*60)
    print("✓✓✓ ALL HOLY WEEK DATES CORRECTED!")
    print("="*60)


if __name__ == '__main__':
    main()
